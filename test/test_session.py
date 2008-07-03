#! /usr/bin/python
# -*- coding: utf-8 -*-

# test/test_session.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for session module
"""

import sys

import scaffold

from gracie import session


class Test_SessionManager(scaffold.TestCase):
    """ Test cases for SessionManager class """

    def setUp(self):
        """ Set up test fixtures """

        self.manager_class = session.SessionManager

    def test_create_session_should_return_session_id(self):
        """ Creating a session should return session ID """
        instance = self.manager_class()
        session_id = instance.create_session()
        self.failIfIs(None, session_id)

    def test_get_session_unknown_id_raises_keyerror(self):
        """ Getting an unknown session ID should raise KeyError """
        instance = self.manager_class()
        session_id = "DECAFBAD"
        self.failUnlessRaises(
            KeyError,
            instance.get_session, session_id
            )

    def test_get_session_returns_same_session(self):
        """ Getting a session by ID should return same username """
        instance = self.manager_class()
        session = dict(
            username = "fred",
            foo = "spam",
            )
        session_id = instance.create_session(session)
        session['session_id'] = session_id
        got_session = instance.get_session(session_id)
        self.failUnlessEqual(session, got_session)

    def test_create_session_should_create_unique_id(self):
        """ Creating a session should create unique ID each time """
        instance = self.manager_class()
        usernames = ["larry", "curly", "moe"]
        sessions = dict()
        for username in usernames:
            session_id = instance.create_session()
            self.failIfIn(sessions, session_id)
            sessions[session_id] = dict(
                session_id = session_id,
                username = username,
                )

    def test_create_multiple_session_for_same_username(self):
        """ Creating multiple sessions for same username should succeed """
        instance = self.manager_class()
        usernames = ["larry", "curly", "moe"]
        sessions = dict()
        for username in usernames:
            for _ in range(10):
                session = dict(username=username)
                session_id = instance.create_session(session)
                session.update(dict(
                    session_id = session_id
                    ))
                sessions[session_id] = session
        for session_id, session in sessions.items():
            got_session = instance.get_session(session_id)
            self.failUnlessEqual(session, got_session)

    def test_remove_session_unknown_should_raise_keyerror(self):
        """ Removing an unknown session ID should raise KeyError """
        instance = self.manager_class()
        session_id = "DECAFBAD"
        self.failUnlessRaises(
            KeyError,
            instance.remove_session, session_id
            )

    def test_remove_session_should_cause_get_session_failure(self):
        """ Removing a session should result in failure to get session """
        instance = self.manager_class()
        identity_name = "fred"
        session_id = instance.create_session()
        instance.remove_session(session_id)
        self.failUnlessRaises(
            KeyError,
            instance.get_session, session_id
            )


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
