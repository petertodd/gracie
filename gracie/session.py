# -*- coding: utf-8 -*-

# gracie/session.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Behaviour for session management
"""

import logging
import random
import sha

# Get the Python logger instance for this module
_logger = logging.getLogger("gracie.session")


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
        message = "%(randnum)s" % vars()
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
