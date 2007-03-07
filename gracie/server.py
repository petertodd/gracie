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
import urlparse
import routes

import pagetemplate
from authservice import PosixAuthService as AuthService
from httpresponse import ResponseHeader, Response

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"

from httpresponse import HTTPResponseCodes as HTTPCodes


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

    def _dispatch(self, route_map):
        """ Dispatch to the appropriate controller """
        controller_map = {
            None: self._make_url_not_found_error_response,
            'identity': self._make_identity_view_response,
        }
        controller_name = None
        if route_map:
            controller_name = route_map['controller']
        controller = controller_map[controller_name]

        response = controller(route_map)
        return response

    def do_GET(self):
        """ Handle a GET command """
        route_map = mapper.match(self.path)
        response = self._dispatch(route_map)
        response.send_to_handler(self)

    def _make_url_not_found_error_response(self, route_map):
        """ Construct a Not Found error response """
        header = ResponseHeader(HTTPCodes.not_found, "Not Found")
        page = pagetemplate.url_not_found_page(self.path)
        data = page.serialise()
        response = Response(header, data)
        return response

    def _make_identity_view_response(self, route_map):
        """ Construct a response for an identity view """
        name = route_map['name']
        try:
            entry = self._server.authservice.get_entry(name)
        except KeyError, e:
            entry = None

        if entry is None:
            header = ResponseHeader(HTTPCodes.not_found, "Not Found")
            page = pagetemplate.identity_user_not_found_page(name)
        else:
            header = ResponseHeader(HTTPCodes.ok)
            page = pagetemplate.identity_view_user_page(entry)

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
