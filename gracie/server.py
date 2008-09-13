# -*- coding: utf-8 -*-

# gracie/server.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Behaviour for OpenID provider server
"""

import sys
import os
import logging
from openid.server.server import Server as OpenIDServer
from openid.store.filestore import FileOpenIDStore as OpenIDStore

from httprequest import HTTPRequestHandler
from httpserver import HTTPServer
from authservice import PamAuthService as AuthService
from authorisation import ConsumerAuthStore
from session import SessionManager
import version

# Get the Python logging instance for this module
_logger = logging.getLogger("gracie.server")


def remove_standard_files():
    """ Close stdin, redirect stdout & stderr to null """
    class NullDevice:
        def write(self, s):
            pass
    sys.stdin.close()
    sys.stdout = NullDevice()
    sys.stderr = NullDevice()

def become_daemon():
    """ Detach the current process and run as a daemon """
    # This technique cribbed from Chad J. Schroeder,
    # <URL:http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/278731>

    pid = os.fork()
    if pid == 0:
        # This is the child of the first fork, so we are now in the
        # background.

        # Set a new process group
        os.setsid()

        pid = os.fork()
        if pid == 0:
            # This is the parent of the new process group, and is
            # orphaned from the original parent process. Good.
            pass
        else:
            # This is the child of the second fork, so we want to exit
            # orphaning the true process to run by itself.
            os._exit(os.EX_OK)
    else:
        # This is the parent process of the first fork
        # so we want to exit, leaving only the child to run
        os._exit(os.EX_OK)

    remove_standard_files()


class GracieServer(object):
    """ Server for Gracie OpenID provider service """

    def __init__(self, socket_params, opts):
        """ Set up a new instance """
        self.version = version.version_full
        self.opts = opts
        self._setup_logging()
        server_address = (opts.host, opts.port)
        self.httpserver = HTTPServer(
            server_address, HTTPRequestHandler, self
            )
        self._setup_openid()
        self.auth_service = AuthService()
        self.sess_manager = SessionManager()
        self.consumer_auth_store = ConsumerAuthStore()

    def _setup_openid(self):
        """ Set up OpenID parameters """
        store = OpenIDStore(self.opts.datadir)
        self.openid_server = OpenIDServer(store)

    def __del__(self):
        _logger.info("Exiting Gracie server")

    def _setup_logging(self):
        """ Set up logging for this server """
        server_version = self.version
        _logger.info(
            "Starting Gracie server (version %(server_version)s)"
            % vars()
            )

    def serve_forever(self):
        """ Begin serving requests indefinitely """
        self.httpserver.serve_forever()
