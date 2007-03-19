# -*- coding: utf-8 -*-

# httprequest.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" HTTP request handling
"""

from BaseHTTPServer import BaseHTTPRequestHandler
import logging
import time
import cgi
import Cookie
import urlparse
import routes
from openid.server.server import BROWSER_REQUEST_MODES

import pagetemplate
from httpresponse import ResponseHeader, Response
from httpresponse import response_codes as http_codes
from authservice import AuthenticationError

session_cookie_name = "gracie_session"


class BaseHTTPRequestHandler(BaseHTTPRequestHandler, object):
    """ Shim to insert base object type into hierarchy """


mapper = routes.Mapper()
mapper.connect('root', '', controller='about', action='view')
mapper.connect('openid', 'openidserver', controller='openid')
mapper.connect('authorise', 'authorise',
               controller='authorise', action='submit')
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
        self.server_version = "Gracie/%(version)s" % locals()

    def log_message(self, format, *args, **kwargs):
        """ Log a message via the server's logger """
        logger = self.gracie_server.logger
        loglevel = logging.INFO
        logger.log(loglevel, format, *args, **kwargs)

    def _make_server_url(self, path):
        """ Construct a URL to a path on this server """
        protocol = "http"
        location = self.server.server_location
        path = path.lstrip("/")
        url = "%(protocol)s://%(location)s/%(path)s" % locals()
        return url

    def _setup_auth_session(self):
        """ Set up the authentication session """
        sess_manager = self.gracie_server.sess_manager
        session_id = self._get_auth_cookie()
        username = None
        try:
            self.session = sess_manager.get_session(session_id)
            username = self.session['username']
        except KeyError:
            self.session = dict()
        else:
            auth_entry = self.gracie_server.auth_service.get_entry(username)
            self.session['auth_entry'] = auth_entry

        if username:
            self.gracie_server.logger.info(
                "Session authenticated as %(username)r" % locals()
            )
        else:
            self.gracie_server.logger.info("Session not authenticated")

    def _remove_auth_session(self):
        """ Remove the authentication session """
        sess_manager = self.gracie_server.sess_manager
        if self.session:
            sess_manager.remove_session(self.session.get('session_id'))
        self.session.clear()

        self.gracie_server.logger.info("Removed authentication session")

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
        field_value = "%(name)s=%(value)s" % locals()
        if expire:
            field_value = (
                "%(field_value)s;Expires=%(expire)s" % locals())
        field = (field_name, field_value)
        response.header.fields.append(field)

    def _set_auth_cookie(self, response):
        """ Set the authentication cookie in the response """
        field_name = "Set-Cookie"
        epoch = time.gmtime(0)
        expire_immediately = time.strftime(
            '%a, %d-%b-%y %H:%M:%S GMT', epoch)

        session_id = self.session.get('session_id')
        if session_id:
            self._set_cookie(response, session_cookie_name, session_id)
        else:
            self._set_cookie(response,
                session_cookie_name, "", expire_immediately
            )

    def _make_openid_url(self, username):
        """ Generate the OpenID URL for a username """
        path = "id/%(username)s" % locals()
        url = self._make_server_url(path)
        return url

    def _get_session_openid_url(self):
        """ Get the OpenID URL for the current session """
        openid_url = None
        if self.session:
            username = self.session.get('username')
            openid_url = self.session.setdefault('openid_url',
                self._make_openid_url(username)
            )
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
            'authorise': self._handle_authorise_request,
        }
        controller_name = None
        if self.route_map:
            controller_name = self.route_map['controller']
        controller = controller_map[controller_name]

        self.gracie_server.logger.info(
            "Dispatching to controller %(controller_name)r" % locals()
        )

        response = controller()
        self._set_auth_cookie(response)
        self._send_response(response)

    def _send_response(self, response):
        """ Send an HTTP response to the user agent """
        response.send_to_handler(self)

        self.gracie_server.logger.info("Sent HTTP response")

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
            self.gracie_server.logger.error(message)
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
            self.gracie_server.logger.info("Received OpenID protocol request")
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
        if self.session:
            openid_url = self._get_session_openid_url()
            if openid_url:
                if openid_url == openid_request.identity:
                    # Session is authenticated for requested identity
                    is_session_identity = True
        consumer_auth_store = self.gracie_server.consumer_auth_store
        identity = openid_request.identity
        trust_root = openid_request.trust_root
        auth_tuple = (identity, trust_root)
        is_authorised = consumer_auth_store.is_authorised(auth_tuple)
        self.gracie_server.logger.info(
            "Checking authorisation to %(identity)r"
            " for site %(trust_root)r" % locals()
        )

        dispatch_map = {
            'checkid_immediate': self._make_checkid_immediate_response,
            'checkid_setup': self._make_checkid_setup_response,
        }
        response = dispatch_map[openid_request.mode](openid_request,
            is_session_identity = is_session_identity,
            is_authorised = is_authorised,
        )

        return response

    def _make_checkid_immediate_response(self, request,
        is_session_identity, is_authorised
    ):
        """ Make a response for an OpenID checkid_immediate request """
        response = None

        if is_session_identity and is_authorised:
            openid_response = request.answer(True)
        else:
            openid_response = request.answer(False,
                self._make_server_url("openidserver")
            )
        response = self._make_response_from_openid_response(
            openid_response
        )

        return response

    def _make_checkid_setup_response(self, request,
        is_session_identity, is_authorised
    ):
        """ Make a response for an OpenID checkid_immediate request """
        response = None

        if is_session_identity and is_authorised:
            openid_response = request.answer(True)
            response = self._make_response_from_openid_response(
                openid_response)
        else:
            if is_session_identity:
                response = \
                    self._make_authorise_consumer_query_response(
                        trust_root = request.trust_root,
                        want_id = request.identity
                    )
            else:
                response = self._make_wrong_authentication_response(
                    request.identity
                )

        return response

    def _make_response_from_openid_response(self, openid_response):
        """ Construct a response to a request to the OpenID server """
        self.gracie_server.logger.info("Delegating response to OpenID library")
        openid_server = self.gracie_server.openid_server
        web_response = openid_server.encodeResponse(openid_response)
        header = ResponseHeader(web_response.code)
        for name, value in web_response.headers.items():
            field = (name, value)
            header.fields.append(field)
        response = Response(header, web_response.body)

        return response

    def _handle_authorise_request(self):
        """ Handle a request to the authorise resource """
        identity = self.query.get('identity', object())
        openid_url = self._get_session_openid_url()
        openid_request = self.session.get('last_openid_request')
        if self.command not in ["POST"]:
            response = self._make_url_not_found_error_response()
        elif openid_url != identity:
            response = self._make_wrong_authentication_response(
                identity
            )
        elif not openid_request:
            message = "No OpenID request for requested authorisation"
            self.gracie_server.logger.warn(message)
            response = self._make_protocol_error_response(message)
        else:
            response = self._handle_authorise_submit_request(
                openid_request
            )

        return response

    def _handle_authorise_submit_request(self, openid_request):
        """ Handle a request to authorise a consumer for an identity """
        self.gracie_server.logger.info(
            "Received consumer authorisation submission"
        )

        status_map = {
            "submit_approve": True,
            "submit_deny": False,
        }

        self.gracie_server.logger.debug("HTTP query: %r" % self.query)
        try:
            trust_root = self.query['trust_root']
            identity = self.query['identity']
            submit_choice = None
            for key in status_map:
                if key in self.query:
                    submit_choice = key
            status = status_map[submit_choice]
        except KeyError, e:
            message = "Malformed authorisation submission"
            self.gracie_server.logger.warn(message)
            response = self._make_protocol_error_response(message)
        else:
            auth_tuple = (identity, trust_root)
            self.gracie_server.consumer_auth_store.store_authorisation(
                (identity, trust_root), status
            )
            self.gracie_server.logger.info(
                "Storing authorisation status %(auth_tuple)r: %(status)r"
                % locals()
            )
            response = self._make_authorise_response(
                openid_request, status
            )

        return response

    def _make_authorise_response(self, openid_request, status):
        """ Construct a response to an authorisation submission """
        openid_response = openid_request.answer(status)
        response = self._make_response_from_openid_response(
            openid_response
        )

        return response


    def _make_redirect_response(self, url):
        """ Construct a response for a redirect """
        header = ResponseHeader(http_codes['found'])
        header.fields.append(("Location", url))
        data = ""
        response = Response(header, data)
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
        header = ResponseHeader(http_codes['internal_error'])
        page = pagetemplate.internal_error_page(message)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_url_not_found_error_response(self):
        """ Construct a Not Found error response """
        header = ResponseHeader(http_codes['not_found'])
        page = pagetemplate.url_not_found_page(self.path)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_protocol_error_response(self, message):
        """ Construct a Protocol Error error response """
        header = ResponseHeader(http_codes['ok'])
        page = pagetemplate.protocol_error_page(message)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_about_site_view_response(self):
        """ Construct a response for the about-this-site view """
        header = ResponseHeader(http_codes['ok'])
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
            header = ResponseHeader(http_codes['not_found'])
            page = pagetemplate.identity_user_not_found_page(name)
        else:
            header = ResponseHeader(http_codes['ok'])
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
        header = ResponseHeader(http_codes['ok'])
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
        header = ResponseHeader(http_codes['ok'])
        page = pagetemplate.login_cancelled_page()
        data = self._get_page_data(page)
        response = Response(header, data)
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
        sess_manager = self.gracie_server.sess_manager
        try:
            username = auth_service.authenticate(credentials)
            authenticated = True
        except AuthenticationError, e:
            authenticated = False
        if authenticated:
            session_id = sess_manager.create_session(dict(
                username = username,
            ))
            self.session = sess_manager.get_session(session_id)
            self.session.update(dict(
                openid_url = self._get_session_openid_url()
            ))
            response = self._make_login_succeeded_response()
        else:
            response = self._make_login_failed_response()
        return response

    def _make_login_failed_response(self):
        """ Construct a response for a failed login request """
        name = self.query.get('username')
        message = "The login details were incorrect."
        header = ResponseHeader(http_codes['ok'])
        page = pagetemplate.login_submit_failed_page(message, name)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_login_succeeded_response(self):
        """ Construct a response for a successful login request """
        root_url = self._make_server_url("")
        response = self._make_redirect_response(root_url)
        return response

    def _make_authorise_consumer_query_response(self,
            trust_root, want_id
    ):
        """ Make a response for query to authorise a consumer """
        header = ResponseHeader(http_codes['ok'])
        page = pagetemplate.authorise_consumer_query_page(
            trust_root = trust_root, want_id_url = want_id
        )
        data = self._get_page_data(page)
        response = Response(header, data)

        return response

    def _make_wrong_authentication_response(self, want_id):
        """ Make a response for action with wrong session auth """
        header = ResponseHeader(http_codes['ok'])
        page = pagetemplate.wrong_authentication_page(
            want_id_url = want_id
        )
        data = self._get_page_data(page)
        response = Response(header, data)

        return response
