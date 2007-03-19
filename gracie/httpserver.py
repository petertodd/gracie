# -*- coding: utf-8 -*-

# httpserver.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Behaviour for HTTP server portion of Gracie
"""

import logging
from BaseHTTPServer import HTTPServer as BaseHTTPServer

import server

# Name of the Python logging instance to use for this module
logger_name = "gracie.httpserver"

default_host = "localhost"
default_port = 8000


class BaseHTTPServer(BaseHTTPServer, object):
    """ Shim to insert base object type into hierarchy """


http_port = 80

def net_location(host, port=None):
    """ Construct a location string from host string and port number """
    if port is None or port == http_port:
        location_spec = "%(host)s"
    else:
        location_spec = "%(host)s:%(port)s"
    location = location_spec % locals()
    return location


class HTTPServer(BaseHTTPServer):
    """ Server for HTTP protocol requests """

    def __init__(self,
            server_address, RequestHandlerClass, gracie_server
    ):
        """ Set up a new instance """
        self.gracie_server = gracie_server
        self._setup_version()
        self._setup_logging()
        super(HTTPServer, self).__init__(
            server_address, RequestHandlerClass
        )
        self._log_location()

    def _setup_version(self):
        """ Set up version string for this server """
        self.version = self.gracie_server.version

    def _setup_logging(self):
        """ Set up logging for this server """
        self.logger = logging.getLogger(logger_name)
        version = self.version
        self.logger.info(
            "Starting Gracie HTTP server (version %(version)s)"
            % locals()
        )

    def server_bind(self):
        """ Bind and name the server """
        super(HTTPServer, self).server_bind()
        self.server_location = net_location(
            self.server_name, self.server_port
        )

    def _log_location(self):
        """ Log the net location of the server """
        location = net_location(*self.server_address)
        self.logger.info(
            "Listening on address %(location)s"
            % locals()
        )

    def handle_request(self):
        """ Handle a single request """
        try:
            super(HTTPServer, self).handle_request()
        except (KeyboardInterrupt, SystemExit), e:
            exc_name = e.__class__.__name__
            message = "Received %(exc_name)s" % locals()
            self.logger.warn(message)
            raise
        except Exception, e:
            message = str(e)
            self.logger.error(message)
            raise
