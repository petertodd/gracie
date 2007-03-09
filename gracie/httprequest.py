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

import pagetemplate
from httpresponse import ResponseHeader, Response
from httpresponse import response_codes as http_codes
from authservice import AuthenticationError
from server import __version__

cookie_name_prefix = "gracie_"


class BaseHTTPRequestHandler(BaseHTTPRequestHandler, object):
    """ Shim to insert base object type into hierarchy """


mapper = routes.Mapper()
mapper.connect('openid', 'openidserver', controller='openid')
mapper.connect('root', '', controller='about', action='view')
mapper.connect('identity', 'id/:name', controller='identity', action='view')
mapper.connect('login', 'login', controller='login', action='view')
mapper.connect('logout', 'logout', controller='logout', action='view')

class HTTPRequestHandler(BaseHTTPRequestHandler):
    """ Handler for individual HTTP requests """

    server_version = "Gracie/%(__version__)s" % globals()

    def __init__(self, request, client_address, server):
        """ Set up a new instance """
        self.server = server
        super(HTTPRequestHandler, self).__init__(
            request, client_address, server
        )

    def log_message(self, format, *args, **kwargs):
        """ Log a message via the server's logger """
        logger = self.server.logger
        loglevel = logging.INFO
        logger.log(loglevel, format, *args, **kwargs)

    def _setup_auth_session(self):
        """ Set up the authentication session """
        self.session_id = None
        self.username = None
        self.auth_entry = None
        session_id = self._get_auth_cookie()
        sess_manager = self.server.sess_manager
        try:
            username = sess_manager.get_session(session_id)
        except KeyError:
            pass
        else:
            self.username = username
            self.session_id = session_id
            auth_service = self.server.auth_service
            self.auth_entry = auth_service.get_entry(username)

        if self.username:
            self.server.logger.info(
                "Authenticated as %s" % self.username
            )
        else:
            self.server.logger.info("Not currently authenticated")

    def _remove_auth_session(self):
        """ Remove the authentication session """
        sess_manager = self.server.sess_manager
        if self.session_id:
            sess_manager.remove_session(self.session_id)
        self.session_id = None
        self.username = None
        self.auth_entry = None

        self.server.logger.info("Removed authentication session")

    def _get_openid_url(self, username):
        """ Generate the OpenID URL for a username """
        url = mapper.generate(controller='identity', action='view',
                              name=username)
        return url

    def _get_cookie(self, name):
        """ Get a cookie from the request """
        value = None
        prefix = cookie_name_prefix
        cookie_string = ";".join(self.headers.getheaders('Cookie'))
        cookies = Cookie.BaseCookie(cookie_string)
        if cookies:
            cookie_name = "%(prefix)s%(name)s" % locals()
            if cookie_name in cookies:
                value = cookies.get(cookie_name).value
        return value

    def _get_auth_cookie(self):
        """ Get the authentication cookie from the request """
        session_id = self._get_cookie('session')
        return session_id

    def _set_cookie(self, response, name, value, expire=None):
        """ Set a cookie in the response header """
        prefix = cookie_name_prefix
        cookie_name = "%(prefix)s%(name)s" % locals()
        field_name = "Set-Cookie"
        field_value = "%(cookie_name)s=%(value)s" % locals()
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
        prefix = cookie_name_prefix

        session_id = self.session_id
        if session_id:
            self._set_cookie(response, 'session', session_id)
        else:
            self._set_cookie(response, 'session', "", expire_immediately)

    def _dispatch(self):
        """ Dispatch to the appropriate controller """
        self.openid_request = None
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

        self.server.logger.info(
            "Dispatching to controller %(controller_name)r" % locals()
        )

        response = controller()
        if self.openid_request:
            self._send_openid_response(response)
        else:
            self._send_http_response(response)

    def _send_http_response(self, response):
        """ Send an HTTP response to the user agent """
        self._set_auth_cookie(response)
        response.send_to_handler(self)

        self.server.logger.info("Sent HTTP response")

    def _send_openid_response(self, response):
        """ Send an OpenID response to the consumer """
        response.send_to_handler(self)

        self.server.logger.info("Sent OpenID protocol response")

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
            self.server.logger.error(message)
            response = self._make_internal_error_response(message)
            self._send_http_response(response)

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
        openid_server = self.server.openid_server
        self.openid_request = openid_server.decodeRequest(self.query)
        if self.openid_request is None:
            response = self._make_about_site_view_response()
        else:
            response = self._make_openid_response()
            
        return response

    def _make_openid_response(self):
        """ Construct a response to a request to the OpenID server """
        self.server.logger.info("Delegating request to OpenID library")
        openid_server = self.server.openid_server
        openid_response = openid_server.handleRequest(
            self.openid_request)
        web_response = openid_server.encodeResponse(
            openid_response)
        header = ResponseHeader(web_response.code)
        header.fields.extend(web_response.headers)
        response = Response(header, web_response.body)

        return response

    def _get_page_data(self, page):
        """ Get the actual data to be used from a page """
        if self.username:
            page.values.update(dict(
                openid_url = self._get_openid_url(self.username),
            ))
        page.values.update(dict(
            auth_entry = self.auth_entry,
            login_url = mapper.generate(
                controller='login', action='view'
            ),
            logout_url = mapper.generate(
                controller='logout', action='view'
            ),
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
            entry = self.server.auth_service.get_entry(name)
        except KeyError, e:
            entry = None

        if entry is None:
            header = ResponseHeader(http_codes['not_found'])
            page = pagetemplate.identity_user_not_found_page(name)
        else:
            header = ResponseHeader(http_codes['ok'])
            page = pagetemplate.identity_view_user_page(entry)

        data = self._get_page_data(page)
        response = Response(header, data)
        return response

    def _make_logout_response(self):
        """ Construct a response for a logout request """
        self._remove_auth_session()
        header = ResponseHeader(http_codes['found'])
        about_url = mapper.generate(controller='about', action='view')
        header.fields.append(("Location", about_url))
        page = pagetemplate.about_site_view_page()
        data = self._get_page_data(page)
        response = Response(header, data)
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
        auth_service = self.server.auth_service
        sess_manager = self.server.sess_manager
        try:
            username = auth_service.authenticate(credentials)
            session_id = sess_manager.create_session(username)
            authenticated = True
        except AuthenticationError, e:
            authenticated = False
        if authenticated:
            self.username = username
            self.session_id = session_id
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
        header = ResponseHeader(http_codes['found'])
        about_url = mapper.generate(controller='about', action='view')
        header.fields.append(("Location", about_url))
        page = pagetemplate.login_auth_succeeded_page(self.username)
        data = self._get_page_data(page)
        response = Response(header, data)
        return response
