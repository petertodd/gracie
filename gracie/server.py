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

import logging
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"


class OpenIDRequestHandler(BaseHTTPRequestHandler, object):
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
        logger.log(format, *args, **kwargs)


class OpenIDServer(HTTPServer):
    """ Server for OpenID protocol requests """

    def __init__(self, server_address, RequestHandlerClass):
        """ Set up a new instance """
        self._setup_logging()
        HTTPServer.__init__(self,
            server_address, RequestHandlerClass)

    def _setup_logging(self):
        """ Set up logging for this server """
        self.logger = logging.getLogger(logger_name)
