# -*- coding: utf-8 -*-

# gracie/httpserver.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Behaviour for HTTP server portion of Gracie
"""

import logging
import urlparse
from BaseHTTPServer import HTTPServer

# Get the Python logging instance for this module
_logger = logging.getLogger("gracie.httpserver")

default_host = "localhost"
default_port = 8000


class BaseHTTPServer(HTTPServer, object):
    """ Shim to insert base object type into hierarchy """


http_port = 80

def net_location(host, port=None):
    """ Construct a location string from host string and port number """
    if port is None or port == http_port:
        location_spec = "%(host)s"
    else:
        location_spec = "%(host)s:%(port)s"
    location = location_spec % vars()
    return location

default_root_url = urlparse.urlunsplit(
    ("http", net_location(default_host, default_port), "/", "", "")
    )


class HTTPServer(BaseHTTPServer):
    """ Server for HTTP protocol requests """

    def __init__(
        self,
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
        version = self.version
        _logger.info(
            "Starting Gracie HTTP server (version %(version)s)"
            % vars()
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
        _logger.info(
            "Listening on address %(location)s"
            % vars()
            )

    def handle_request(self):
        """ Handle a single request """
        try:
            super(HTTPServer, self).handle_request()
        except (KeyboardInterrupt, SystemExit), e:
            exc_name = e.__class__.__name__
            message = "Received %(exc_name)s" % vars()
            _logger.warn(message)
            raise
        except Exception, e:
            message = str(e)
            _logger.error(message)
            raise
