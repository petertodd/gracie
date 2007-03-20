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
import random
import sha
from openid.server.server import Server as OpenIDServer
from openid.store.filestore import FileOpenIDStore as OpenIDStore

from httprequest import HTTPRequestHandler
from httpserver import HTTPServer, default_host, default_port
from authservice import PamAuthService as AuthService

__version__ = "0.0"

# Name of the Python logging instance to use for this module
logger_name = "gracie.server"


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

    def _generate_session_id(self):
        """ Generate a unique session ID """
        randnum = self._rng.random()
        message = "%(randnum)s" % locals()
        message_hash = sha.sha(message)
        session_id = message_hash.hexdigest()
        return session_id

    def create_session(self, session=None):
        """ Create a new session for supplied session dict """
        if session is None:
            session = dict()
        session_id = self._generate_session_id()
        session['session_id'] = session_id
        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id):
        """ Get the session for specified session ID """
        session = self._sessions[session_id]
        return session

    def remove_session(self, session_id):
        """ Remove the specified session """
        del self._sessions[session_id]


class ConsumerAuthStore(object):
    """ Storage for consumer request authorisations """

    def __init__(self):
        """ Set up a new instance """
        self._authorisations = dict()

    def is_authorised(self, auth_tuple):
        """ Report authorisation of an (identity, known_root) tuple """
        is_authorised = self._authorisations.get(
            auth_tuple, False)
        return is_authorised

    def store_authorisation(self, auth_tuple, status):
        """ Store an authorisation status """
        self._authorisations[auth_tuple] = status

    def remove_authorisation(self, auth_tuple):
        """ Remove an authorisation status """
        if auth_tuple in self._authorisations:
            del self._authorisations[auth_tuple]


class GracieServer(object):
    """ Server for Gracie OpenID provider service """

    def __init__(self, server_address, opts):
        """ Set up a new instance """
        self.version = __version__
        self.opts = opts
        self._setup_logging()
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
        self.logger.info("Exiting Gracie server")

    def _setup_logging(self):
        """ Set up logging for this server """
        self.logger = logging.getLogger(logger_name)
        server_version = __version__
        self.logger.info(
            "Starting Gracie server (version %(server_version)s)"
            % locals()
        )

    def serve_forever(self):
        """ Begin serving requests indefinitely """
        self.httpserver.serve_forever()
