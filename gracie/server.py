# -*- coding: utf-8 -*-

# server.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Behaviour for OpenID provider server
"""

import sys
import logging
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import cgi
import Cookie
import urlparse
import routes
import time
import random
import sha

import pagetemplate
from authservice import PamAuthService as AuthService
from authservice import AuthenticationError
from httpresponse import ResponseHeader, Response
from httpresponse import response_codes as http_codes

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"

cookie_name_prefix = "gracie_"


class HTTPServer(HTTPServer, object):
    """ Shim to insert base object type into hierarchy """

class BaseHTTPRequestHandler(BaseHTTPRequestHandler, object):
    """ Shim to insert base object type into hierarchy """


http_port = 80

def net_location(host, port=None):
    """ Construct a location string from host string and port number """
    port_spec = ":%(port)s" % locals()
    if port is None or port == http_port:
        location_spec = "%(host)s"
    else:
        location_spec = "%(host)s:%(port)s"
    location = location_spec % locals()
    return location

default_host = "localhost"
default_port = 8000
default_location = net_location(default_host, default_port)


mapper = routes.Mapper()
mapper.connect('root', '', controller='about', action='view')
mapper.connect('identity', 'id/:name', controller='identity', action='view')
mapper.connect('login', 'login', controller='login', action='view')
mapper.connect('logout', 'logout', controller='logout', action='view')

class OpenIDRequestHandler(BaseHTTPRequestHandler):
    """ Handler for individual OpenID requests """

    server_version = "Gracie/%(__version__)s" % globals()

    def __init__(self, request, client_address, server):
        """ Set up a new instance """
        self._server = server
        super(OpenIDRequestHandler, self).__init__(
            request, client_address, server
        )

    def log_message(self, format, *args, **kwargs):
        """ Log a message via the server's logger """
        logger = self._server.logger
        loglevel = logging.INFO
        logger.log(loglevel, format, *args, **kwargs)

    def _setup_auth_session(self):
        """ Set up the authentication session """
        self.username = None
        self.session_id = None
        self.auth_entry = None
        (username, session) = self._get_auth_cookie()
        try:
            session_id = self._server.get_auth_session(username)
        except KeyError:
            pass
        else:
            if session == session_id:
                self.username = username
                self.session_id = session_id
                auth_service = self._server.authservice
                self.auth_entry = auth_service.get_entry(username)

    def _remove_auth_session(self):
        """ Remove the authentication session """
        if self.username:
            self._server.remove_auth_session(self.username)
        self.username = None
        self.session_id = None
        self.auth_entry = None

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
        username = self._get_cookie('username')
        session_id = self._get_cookie('session')
        return (username, session_id)

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

        username = self.username
        if username:
            self._set_cookie(response, 'username', username)
        else:
            self._set_cookie(response, 'username', "", expire_immediately)

        session_id = self.session_id
        if session_id:
            self._set_cookie(response, 'session', session_id)
        else:
            self._set_cookie(response, 'session', "", expire_immediately)

    def _dispatch(self):
        """ Dispatch to the appropriate controller """
        controller_map = {
            None: self._make_url_not_found_error_response,
            'about': self._make_about_site_view_response,
            'identity': self._make_identity_view_response,
            'logout': self._make_logout_response,
            'login': self._make_login_response,
        }
        controller_name = None
        if self.route_map:
            controller_name = self.route_map['controller']
        controller = controller_map[controller_name]

        response = controller()
        self._set_auth_cookie(response)
        response.send_to_handler(self)

    def _parse_path(self):
        """ Parse the request path """
        keys = ('scheme', 'location', 'path', 'query', 'fragment')
        values = urlparse.urlsplit(self.path)
        self.parsed_url = dict(zip(keys, values))
        self.route_map = mapper.match(self.path)

    def _parse_query(self):
        """ Parse query fields from the request data """
        self.query = {}
        for key, value in cgi.parse_qsl(self.query_data):
            self.query[key] = value

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
            entry = self._server.authservice.get_entry(name)
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
        authenticate = self._server.authservice.authenticate
        try:
            username = authenticate(credentials)
            session_id = self._server.create_auth_session(username)
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


class OpenIDServer(HTTPServer):
    """ Server for OpenID protocol requests """

    def __init__(self, server_address, RequestHandlerClass):
        """ Set up a new instance """
        self._setup_logging()
        super(OpenIDServer, self).__init__(
            server_address, RequestHandlerClass
        )
        self.authservice = AuthService()
        self._init_session_generator()
        self._auth_sessions = dict()

    def _setup_logging(self):
        """ Set up logging for this server """
        self.logger = logging.getLogger(logger_name)

    def _init_session_generator(self):
        """ Initialise the session ID generator """
        self._rng = random.Random()
        self._rng.seed()

    def _generate_session_id(self, username):
        """ Generate a session ID for the specified username """
        randnum = self._rng.random()
        message = "%(username)s:%(randnum)s" % locals()
        message_hash = sha.sha(message)
        session_id = message_hash.hexdigest()
        return session_id

    def create_auth_session(self, username):
        """ Create a new authentication session """
        session_id = self._generate_session_id(username)
        self._auth_sessions[username] = session_id
        return session_id

    def get_auth_session(self, username):
        """ Get the session ID for specified username """
        session_id = self._auth_sessions[username]
        return session_id

    def remove_auth_session(self, username):
        """ Get the session ID for specified username """
        del self._auth_sessions[username]
