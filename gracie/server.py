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
import traceback

Page = object

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"

from http_response import HTTPResponseCodes as HTTPCodes


class HTTPServer(HTTPServer, object):
    """ Shim to insert base object type into hierarchy """

class BaseHTTPRequestHandler(BaseHTTPRequestHandler, object):
    """ Shim to insert base object type into hierarchy """


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

    def _get_url_params(self):
        """ Get the component parameters from the requested URL """
        keys = [
            'scheme', 'location', 'path', 'query', 'fragment_id',
        ]
        values = urlparse.urlsplit(self.path)
        params = dict(zip(keys, values))
        return params

    def do_GET(self):
        """ Handle a GET command """
        self.url_params = self._get_url_params()
        path = self.url_params['path']
        if path.startswith("/id/"):
            identity = path[4:]
            page_data = self._make_identity_page(identity)
            self.send_response(HTTPCodes.ok)
            self.end_headers()
            self.wfile.write(page_data)

    def _make_identity_page(self, identity):
        """ Construct a page for an identity """
        page_title = "Identity page for %(identity)s" % locals()
        page = self.server.PageClass(title=page_title)
        page_data = page.serialise()
        return page_data


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
