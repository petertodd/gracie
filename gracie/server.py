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
from BaseHTTPServer import HTTPServer as BaseHTTPServer
import random
import sha
from openid.server.server import Server as OpenIDServer
from openid.store.dumbstore import DumbStore as OpenIDStore

from authservice import PamAuthService as AuthService

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"


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

default_host = "localhost"
default_port = 8000
default_location = net_location(default_host, default_port)


class SessionManager(object):
    """ Manage user sessions across transactions """

    def __init__(self):
        """ Set up a new instance """
        self._init_session_generator()

    def _init_session_generator(self):
        """ Initialise the session ID generator """
        self._rng = random.Random()
        self._rng.seed()
        self._sessions = dict()

    def _generate_session_id(self, username):
        """ Generate a session ID for the specified username """
        randnum = self._rng.random()
        message = "%(username)s:%(randnum)s" % locals()
        message_hash = sha.sha(message)
        session_id = message_hash.hexdigest()
        return session_id

    def create_session(self, username):
        """ Create a new session for username """
        session_id = self._generate_session_id(username)
        self._sessions[session_id] = username
        return session_id

    def get_session(self, session_id):
        """ Get the username for specified session ID """
        username = self._sessions[session_id]
        return username

    def remove_session(self, session_id):
        """ Remove the specified session """
        del self._sessions[session_id]


class HTTPServer(BaseHTTPServer):
    """ Server for HTTP protocol requests """

    def __init__(self, server_address, RequestHandlerClass):
        """ Set up a new instance """
        self._setup_logging()
        super(HTTPServer, self).__init__(
            server_address, RequestHandlerClass
        )
        self._setup_openid()
        self.auth_service = AuthService()
        self.sess_manager = SessionManager()

    def server_bind(self):
        """ Bind and name the server """
        super(HTTPServer, self).server_bind()
        self.server_location = net_location(
            self.server_name, self.server_port
        )

    def _setup_openid(self):
        """ Set up OpenID parameters """
        secret = "gracie"
        store = OpenIDStore(secret)
        self.openid_server = OpenIDServer(store)

    def __del__(self):
        self.logger.info("Exiting Gracie server")

    def _setup_logging(self):
        """ Set up logging for this server """
        self.logger = logging.getLogger(logger_name)
        server_version = __version__
        self.logger.info(
            "Starting Gracie server (version %(server_version)s)"
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
