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

Page = object

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"

from http_response import HTTPResponseCodes as HTTPCodes


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
            'identity': self._make_identity_page,
        }
        controller = controller_map[route_map['controller']]
        response = controller(route_map)
        return response

    def do_GET(self):
        """ Handle a GET command """
        route_map = mapper.match(self.path)
        if route_map:
            response = self._dispatch(route_map)
        else:
            response = self._make_error_page(HTTPCodes.not_found)

        code, message = (response.get('code', HTTPCodes.ok),
                         response.get('message'))
        self.send_response(code, message)
        self.end_headers()
        self.wfile.write(response['data'])

    def _make_error_page(self, code):
        """ Construct an error page """
        page = self.server.PageClass(title="Not found")
        page_data = page.serialise()
        response = dict(code=code, message="Not found", data=page_data)
        return response

    def _make_identity_page(self, route_map):
        """ Construct a page for an identity """
        name = route_map['name']
        page_title = "Identity page for %(name)s" % locals()
        page = self.server.PageClass(title=page_title)
        page_data = page.serialise()
        response = dict(data=page_data)
        return response


class OpenIDServer(HTTPServer):
    """ Server for OpenID protocol requests """

    def __init__(self, server_address, RequestHandlerClass):
        """ Set up a new instance """
        self._setup_logging()
        super(OpenIDServer, self).__init__(
            server_address, RequestHandlerClass
        )
        self.PageClass = Page

    def _setup_logging(self):
        """ Set up logging for this server """
        self.logger = logging.getLogger(logger_name)
