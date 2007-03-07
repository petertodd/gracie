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
import urlparse
import routes

import pagetemplate
from authservice import PosixAuthService as AuthService
from httpresponse import ResponseHeader, Response
from httpresponse import response_codes as http_codes

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"


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
mapper.connect('identity', 'id/:name', controller='identity', action='view')
mapper.connect('login', 'login', controller='login')

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

    def _dispatch(self):
        """ Dispatch to the appropriate controller """
        controller_map = {
            None: self._make_url_not_found_error_response,
            'identity': self._make_identity_view_response,
            'login': self._make_login_response,
        }
        controller_name = None
        if self.route_map:
            controller_name = self.route_map['controller']
        controller = controller_map[controller_name]

        response = controller()
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
        self._parse_path()
        self.query_data = self.parsed_url['query']
        self._parse_query()
        self._dispatch()

    def do_POST(self):
        """ Handle a POST request """
        self.route_map = mapper.match(self.path)
        content_length = int(self.headers['Content-Length'])
        self.query_data = self.rfile.read(content_length)
        self._parse_query()
        self._dispatch()

    def _make_url_not_found_error_response(self):
        """ Construct a Not Found error response """
        header = ResponseHeader(http_codes['not_found'])
        page = pagetemplate.url_not_found_page(self.path)
        data = page.serialise()
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

        data = page.serialise()
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
        data = page.serialise()
        response = Response(header, data)
        return response

    def _make_login_submit_response(self):
        """ Construct a response for a login submit request """
        name = self.query.get('username')
        message = "The login details were incorrect."
        header = ResponseHeader(http_codes['ok'])
        page = pagetemplate.login_submit_failed_page(message, name)
        data = page.serialise()
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

    def _setup_logging(self):
        """ Set up logging for this server """
        self.logger = logging.getLogger(logger_name)
