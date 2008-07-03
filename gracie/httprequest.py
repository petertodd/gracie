# -*- coding: utf-8 -*-

# gracie/httprequest.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" HTTP request handling
"""

import BaseHTTPServer
import logging
import time
import cgi
import Cookie
import urlparse
import routes
from openid.server.server import BROWSER_REQUEST_MODES

from gracie import pagetemplate
from gracie.httpresponse import ResponseHeader, Response
from gracie.httpresponse import response_codes as http_codes
from gracie.authservice import AuthenticationError

session_cookie_name = "gracie_session"

_logger = logging.getLogger("gracie.httprequest")


class BaseHTTPRequestHandler(
    BaseHTTPServer.BaseHTTPRequestHandler,
    object):
    """ Shim to insert base object type into hierarchy """


mapper = routes.Mapper()
mapper.connect('root', '', controller='about', action='view')
mapper.connect('openid', 'openidserver', controller='openid')
mapper.connect('identity', 'id/:name',
               controller='identity', action='view')
mapper.connect('login', 'login', controller='login', action='view')
mapper.connect('logout', 'logout', controller='logout', action='view')

class HTTPRequestHandler(BaseHTTPRequestHandler):
    """ Handler for individual HTTP requests """

    def __init__(self, request, client_address, server):
        """ Set up a new instance """
        self.gracie_server = server.gracie_server
        self._setup_version()
        super(HTTPRequestHandler, self).__init__(
            request, client_address, server
            )

    def _setup_version(self):
        """ Set up the version string """
        version = self.gracie_server.version
        self.server_version = "Gracie/%(version)s" % vars()

    def log_message(self, format, *args, **kwargs):
        """ Log a message via the server's logger """
        logger = _logger
        loglevel = logging.INFO
        logger.log(loglevel, format, *args, **kwargs)

    def _make_server_url(self, path):
        """ Construct a URL to a path on this server """
        root_url = self.gracie_server.opts.root_url
        url = urlparse.urljoin(root_url, path)
        return url

    def _begin_new_session(self):
        """ Begin a new server session """
        sess_manager = self.gracie_server.sess_manager
        self.session = dict()
        session_id = sess_manager.create_session(self.session)
        self.session['session_id'] = session_id

    def _authenticate_session(self, username):
        """ Authenticate the current session as specified username """
        if username is not None:
            auth_entry = self.gracie_server.auth_service.get_entry(username)
            self.session.update(dict(
                username = username,
                auth_entry = auth_entry,
                ))
            _logger.info(
                "Session authenticated as %(username)r" % vars()
                )
        else:
            _logger.info("Session not authenticated")

    def _setup_auth_session(self):
        """ Set up the authentication session """
        sess_manager = self.gracie_server.sess_manager
        session_id = self._get_auth_cookie()
        try:
            self.session = sess_manager.get_session(session_id)
        except KeyError:
            self._begin_new_session()

        username = self.session.get('username')
        self._authenticate_session(username)

    def _remove_auth_session(self):
        """ Remove the authentication session """
        sess_manager = self.gracie_server.sess_manager
        if self.session:
            sess_manager.remove_session(self.session.get('session_id'))
        self._begin_new_session()

        _logger.info("Removed authentication session")

    def _get_cookie(self, name):
        """ Get a cookie from the request """
        value = None
        cookie_string = ";".join(self.headers.getheaders('Cookie'))
        cookies = Cookie.BaseCookie(cookie_string)
        if cookies:
            if session_cookie_name in cookies:
                value = cookies[session_cookie_name].value
        return value

    def _get_auth_cookie(self):
        """ Get the authentication cookie from the request """
        session_id = self._get_cookie('session')
        return session_id

    def _set_cookie(self, response, name, value, expire=None):
        """ Set a cookie in the response header """
        field_name = "Set-Cookie"
        field_value = "%(name)s=%(value)s" % vars()
        if expire:
            field_value = (
                "%(field_value)s;Expires=%(expire)s" % vars())
        field = (field_name, field_value)
        response.header.fields.append(field)

    def _set_auth_cookie(self, response):
        """ Set the authentication cookie in the response """
        field_name = "Set-Cookie"
        epoch = time.gmtime(0)
        expire_immediately = time.strftime(
            '%a, %d-%b-%y %H:%M:%S GMT', epoch)

        session_id = self.session['session_id']
        self._set_cookie(response, session_cookie_name, session_id)

    def _get_username_from_identity(self, identity):
        """ Parse a local username from an OpenID URL """
        name = None
        (_, _, path, _, _) = urlparse.urlsplit(identity)
        route_map = mapper.match(path)
        if route_map:
            if route_map.get('controller') == 'identity':
                name = route_map.get('name')
        return name

    def _make_openid_url(self, username):
        """ Generate the OpenID URL for a username """
        path = "id/%(username)s" % vars()
        url = self._make_server_url(path)
        return url

    def _get_session_openid_url(self):
        """ Get the OpenID URL for the current session """
        openid_url = None
        if self.session:
            username = self.session.get('username')
            openid_url = self._make_openid_url(username)
            self.session['openid_url'] = openid_url
        return openid_url

    def _get_session_auth_entry(self):
        auth_entry = None
        if self.session:
            auth_entry = self.session.get('auth_entry')
        return auth_entry

    def _dispatch(self):
        """ Dispatch to the appropriate controller """
        controller_map = {
            None: self._make_url_not_found_error_response,
            'openid': self._handle_openid_request,
            'about': self._make_about_site_view_response,
            'identity': self._make_identity_view_response,
            'logout': self._make_logout_response,
            'login': self._make_login_response,
            }
        controller_name = None
        if self.route_map:
            controller_name = self.route_map['controller']
        controller = controller_map[controller_name]

        _logger.info(
            "Dispatching to controller %(controller_name)r" % vars()
            )

        response = controller()
        self._set_auth_cookie(response)
        self._send_response(response)

    def _send_response(self, response):
        """ Send an HTTP response to the user agent """
        response.send_to_handler(self)

        _logger.info("Sent HTTP response")

    def _parse_path(self):
        """ Parse the request path """
        keys = ('scheme', 'location', 'path', 'query', 'fragment')
        values = urlparse.urlsplit(self.path)
        self.parsed_url = dict(zip(keys, values))
        self.route_map = mapper.match(self.parsed_url['path'])

    def _parse_query(self):
        """ Parse query fields from the request data """
        self.query = {}
        for key, value in cgi.parse_qsl(self.query_data):
            self.query[key] = value

    def handle(self):
        """ Handle the requests """
        try:
            super(HTTPRequestHandler, self).handle()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            message = str(e)
            _logger.error(message)
            response = self._make_internal_error_response(message)
            self._send_response(response)
            raise

    def do_GET(self):
        """ Handle a GET request """
        self._setup_auth_session()
        self._parse_path()
        self.query_data = self.parsed_url['query']
        self._parse_query()
        self._dispatch()

    def do_POST(self):
        """ Handle a POST request """
        self._setup_auth_session()
        self.route_map = mapper.match(self.path)
        content_length = int(self.headers['Content-Length'])
        self.query_data = self.rfile.read(content_length)
        self._parse_query()
        self._dispatch()

    def _handle_openid_request(self):
        """ Handle a request to the OpenID server URL """
        openid_server = self.gracie_server.openid_server
        openid_request = openid_server.decodeRequest(self.query)
        if openid_request is None:
            response = self._make_about_site_view_response()
        else:
            _logger.info("Received OpenID protocol request")
            self.session['last_openid_request'] = openid_request
            if openid_request.mode in BROWSER_REQUEST_MODES:
                response = self._handle_openid_browser_request(
                    openid_request
                    )
            else:
                openid_response = openid_server.handleRequest(
                    openid_request
                    )
                response = self._make_response_from_openid_response(
                    openid_response
                    )

        return response

    def _handle_openid_browser_request(self, openid_request):
        """ Handle an OpenID request with user-agent interaction """
        is_session_identity = False
        identity = openid_request.identity
        if self.session:
            openid_url = self._get_session_openid_url()
            if openid_url:
                if openid_url == identity:
                    # Session is authenticated for requested identity
                    is_session_identity = True

        dispatch_map = {
            'checkid_immediate': self._make_checkid_immediate_response,
            'checkid_setup': self._make_checkid_setup_response,
            }
        response = dispatch_map[openid_request.mode](
            openid_request,
            is_session_identity=is_session_identity,
            )

        return response

    def _make_checkid_immediate_response(
        self, request,
        is_session_identity,
        ):
        """ Make a response for an OpenID checkid_immediate request """
        response = None

        if is_session_identity:
            openid_response = request.answer(True)
        else:
            openid_response = request.answer(
                False,
                self._make_server_url("openidserver")
                )
        response = self._make_response_from_openid_response(
            openid_response
            )

        return response

    def _make_checkid_setup_response(
        self, request,
        is_session_identity,
        ):
        """ Make a response for an OpenID checkid_setup request """
        response = None

        if is_session_identity:
            openid_response = request.answer(True)
            response = self._make_response_from_openid_response(
                openid_response
                )
        else:
            response = self._make_wrong_authentication_response(
                request.identity
                )

        return response

    def _make_response_from_openid_response(self, openid_response):
        """ Construct a response to a request to the OpenID server """
        _logger.info("Delegating response to OpenID library")
        openid_server = self.gracie_server.openid_server
        web_response = openid_server.encodeResponse(openid_response)
        header = ResponseHeader(web_response.code)
        for name, value in web_response.headers.items():
            field = (name, value)
            header.fields.append(field)
        response = Response(header, web_response.body)

        return response

    def _make_url_from_openid_response(self, openid_response):
        """ Construct a URL corresponding to an OpenID response """
        _logger.info("Getting URL for OpenID response")
        url = openid_response.encodeToURL()
        return url

    def _make_redirect_response(self, url):
        """ Construct a response for a redirect """
        header = ResponseHeader(http_codes["Found"])
        header.fields.append(("Location", url))
        data = ""
        response = Response(header, data)
        _logger.info("Redirecting to %(url)r" % vars())
        return response

    def _get_page_data(self, page):
        """ Get the actual data to be used from a page """
        page.values.update(dict(
            server_version = self.server_version,
            server_location = self.server.server_location,
            auth_entry = self._get_session_auth_entry(),
            openid_url = self._get_session_openid_url(),
            root_url = self._make_server_url(""),
            server_url = self._make_server_url("openidserver"),
            login_url = self._make_server_url("login"),
            logout_url = self._make_server_url("logout"),
            ))
        return page.serialise()

    def _make_internal_error_response(self, message):
        """ Construct an Internal Error error response """
        header = ResponseHeader(http_codes["Internal Server Error"])
        page = pagetemplate.internal_error_page(message)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_url_not_found_error_response(self):
        """ Construct a Not Found error response """
        header = ResponseHeader(http_codes["Not Found"])
        page = pagetemplate.url_not_found_page(self.path)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_protocol_error_response(self, message):
        """ Construct a Protocol Error error response """
        header = ResponseHeader(http_codes["OK"])
        page = pagetemplate.protocol_error_page(message)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_about_site_view_response(self):
        """ Construct a response for the about-this-site view """
        header = ResponseHeader(http_codes["OK"])
        page = pagetemplate.about_site_view_page()
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_identity_view_response(self):
        """ Construct a response for an identity view """
        name = self.route_map['name']
        try:
            entry = self.gracie_server.auth_service.get_entry(name)
        except KeyError, e:
            entry = None

        if entry is None:
            header = ResponseHeader(http_codes["Not Found"])
            page = pagetemplate.identity_user_not_found_page(name)
        else:
            header = ResponseHeader(http_codes["OK"])
            identity_url = self._make_openid_url(name)
            page = pagetemplate.identity_view_user_page(
                entry, identity_url
                )

        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_logout_response(self):
        """ Construct a response for a logout request """
        self._remove_auth_session()

        root_url = self._make_server_url("")
        response = self._make_redirect_response(root_url)
        return response

    def _make_login_response(self):
        """ Construct a response for a login request """
        controller = {
            'GET': self._make_login_view_response,
            'POST': self._make_login_submit_response,
            }[self.command]
        response = controller()
        return response

    def _make_login_view_response(self):
        """ Construct a response for a login view request """
        header = ResponseHeader(http_codes["OK"])
        page = pagetemplate.login_view_page()
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_login_submit_response(self):
        """ Construct a response for a login submit request """
        if 'cancel' in self.query:
            response = self._make_login_cancelled_response()
        elif 'submit' in self.query:
            response = self._make_login_authenticate_response()
        else:
            response = self._make_url_not_found_error_response()
        return response

    def _make_login_cancelled_response(self):
        """ Construct a response for a login cancel request """
        root_url = self._make_server_url("")
        openid_request = self.session.get('last_openid_request')
        if openid_request:
            return_url = self._make_url_from_openid_response(
                openid_request.answer(False)
                )
        else:
            return_url = root_url
        response = self._make_redirect_response(return_url)
        return response

    def _make_login_authenticate_response(self):
        """ Construct a response for a login authenticate request """
        want_username = self.query.get('username')
        password = self.query.get('password')
        credentials = dict(
            username=want_username,
            password=password
            )
        auth_service = self.gracie_server.auth_service
        try:
            username = auth_service.authenticate(credentials)
            authenticated = True
        except AuthenticationError, e:
            authenticated = False
        if authenticated:
            self._authenticate_session(username)
            response = self._make_login_succeeded_response()
        else:
            response = self._make_login_failed_response()
        return response

    def _make_login_failed_response(self):
        """ Construct a response for a failed login request """
        name = self.query.get('username')
        message = "The login details were incorrect."
        header = ResponseHeader(http_codes["OK"])
        page = pagetemplate.login_submit_failed_page(message, name)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_login_succeeded_response(self):
        """ Construct a response for a successful login request """
        root_url = self._make_server_url("")
        openid_request = self.session.get('last_openid_request')
        openid_url = self._get_session_openid_url()
        if openid_request:
            if openid_request.identity == openid_url:
                openid_server = self.server.gracie_server.openid_server
                openid_response = openid_server.signatory.sign(
                    openid_request.answer(True)
                    )
                return_url = self._make_url_from_openid_response(
                    openid_response
                    )
                response = self._make_redirect_response(return_url)
            else:
                response = self._make_wrong_authentication_response(
                    openid_request.identity
                    )
        else:
            response = self._make_redirect_response(root_url)
        return response

    def _make_wrong_authentication_response(self, want_id):
        """ Make a response for action with wrong session auth """
        want_username = self._get_username_from_identity(want_id)
        header = ResponseHeader(http_codes["OK"])
        page = pagetemplate.wrong_authentication_page(
            want_username = want_username,
            want_id_url = want_id
            )
        data = self._get_page_data(page)
        response = Response(header, data)

        return response
