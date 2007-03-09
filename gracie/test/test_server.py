#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test_server.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for server module
"""

import sys
import os
from StringIO import StringIO
import logging

import scaffold
from scaffold import Mock
from test_authservice import Stub_AuthService
from test_httpresponse import Stub_ResponseHeader, Stub_Response

import server


class Test_net_location(scaffold.TestCase):
    """ Test cases for net_location function """

    def test_combines_components_to_location(self):
        """ net_location() should combine components to net location """
        locations = {
            ("foo", None): "foo",
            ("foo", 80): "foo",
            ("foo", 81): "foo:81",
        }

        for (host, port), expect_location in locations.items():
            location = server.net_location(host, port)
            self.failUnlessEqual(expect_location, location)


class Test_SessionManager(scaffold.TestCase):
    """ Test cases for SessionManager class """

    def setUp(self):
        """ Set up test fixtures """

        self.manager_class = server.SessionManager

    def test_create_session_should_return_session_id(self):
        """ Creating a session should return session ID """
        instance = self.manager_class()
        identity_name = "fred"
        session_id = instance.create_session(identity_name)
        self.failUnless(session_id is not None)

    def test_get_session_unknown_id_raises_keyerror(self):
        """ Getting an unknown session ID should raise KeyError """
        instance = self.manager_class()
        session_id = "DECAFBAD"
        self.failUnlessRaises(KeyError,
            instance.get_session, session_id
        )

    def test_get_session_returns_same_username(self):
        """ Getting a session by ID should return same username """
        instance = self.manager_class()
        identity_name = "fred"
        session_id = instance.create_session(identity_name)
        got_name = instance.get_session(session_id)
        self.failUnlessEqual(identity_name, got_name)

    def test_create_session_should_create_unique_id(self):
        """ Creating a session should create unique ID each time """
        instance = self.manager_class()
        usernames = ["larry", "curly", "moe"]
        sessions = dict()
        for username in usernames:
            session_id = instance.create_session(username)
            self.failIf(session_id in sessions,
                "Session ID %(session_id)r already exists"
                " in %(sessions)r" % locals()
            )

    def test_create_multiple_session_for_same_username(self):
        """ Creating multiple sessions for same username should succeed """
        instance = self.manager_class()
        usernames = ["larry", "curly", "moe"]
        sessions = dict()
        for username in usernames:
            for _ in range(10):
                session_id = instance.create_session(username)
                sessions[session_id] = username
        for session_id, username in sessions.items():
            got_username = instance.get_session(session_id)
            self.failUnlessEqual(username, got_username)

    def test_remove_session_unknown_should_raise_keyerror(self):
        """ Removing an unknown session ID should raise KeyError """
        instance = self.manager_class()
        session_id = "DECAFBAD"
        self.failUnlessRaises(KeyError,
            instance.remove_session, session_id
        )

    def test_remove_session_should_cause_get_session_failure(self):
        """ Removing a session should result in failure to get session """
        instance = self.manager_class()
        identity_name = "fred"
        session_id = instance.create_session(identity_name)
        instance.remove_session(session_id)
        self.failUnlessRaises(KeyError,
            instance.get_session, session_id
        )


class Stub_HTTPRequestHandler(object):
    """ Stub class for HTTPRequestHandler """

class Stub_OpenIDError(Exception):
    """ Stub error class for openid module """

class Stub_OpenIDStore(object):
    """ Stub class for openid backing store """

    def __init__(self, _, *args, **kwargs):
        """ Set up a new instance """

class Stub_OpenIDServer(object):
    """ Stub class for an OpenID protocol server """

    def __init__(self, store):
        """ Set up a new instance """
        if not isinstance(
            store, (Stub_OpenIDStore, server.OpenIDStore)):
            raise ValueError("store must be an OpenIDStore instance")

class Stub_OpenIDResponse(object):
    """ Stub class for an OpenID protocol response """

    def __init__(self):
        self.code = 200
        self.headers = [("openid", "yes")]
        self.body = "OpenID response"


def stub_server_bind(server):
    """ Stub method to get server location """
    (host, port) = server.server_address
    (server.server_name, server.server_port) = (host, port)

class Test_HTTPServer(scaffold.TestCase):
    """ Test cases for HTTPServer class """

    def setUp(self):
        """ Set up test fixtures """

        self.server_class = server.HTTPServer

        self.stub_handler_class = Stub_HTTPRequestHandler
        self.mock_handler_class = Mock('HTTPRequestHandler')

        self.openid_server_prev = server.OpenIDServer
        self.openid_store_prev = server.OpenIDStore
        server.OpenIDServer = Stub_OpenIDServer
        server.OpenIDStore = Stub_OpenIDStore

        self.server_bind_prev = server.BaseHTTPServer.server_bind
        server.BaseHTTPServer.server_bind = stub_server_bind

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.valid_servers = {
            'simple': dict(
                address = ('', 80),
            ),
        }

        for key, params in self.valid_servers.items():
            args = params.get('args')
            address = params.get('address')
            handler_class = params.setdefault(
                'handler_class', self.stub_handler_class)
            if not args:
                args = dict(
                    server_address = address,
                    RequestHandlerClass = handler_class
                )
            instance = self.server_class(**args)
            params['args'] = args
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_servers
        )

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        server.OpenIDServer = self.openid_server_prev
        server.OpenIDStore = self.openid_store_prev
        server.BaseHTTPServer.server_bind = self.server_bind_prev

    def test_instantiate(self):
        """ New HTTPServer instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_logger_name_as_specified(self):
        """ HTTPServer should have logger of specified name """
        params = self.valid_servers['simple']
        logger_name_prev = server.logger_name
        logger_name_test = "Foo.Bar"
        server.logger_name = logger_name_test
        expect_logger = logging.getLogger(logger_name_test)
        instance = self.server_class(**params['args'])
        self.failUnlessEqual(expect_logger, instance.logger)
        server.logger_name = logger_name_prev

    def test_request_handler_class_as_specified(self):
        """ HTTPServer should have specified RequestHandlerClass """
        for key, params in self.iterate_params():
            instance = params['instance']
            handler_class = params['handler_class']
            self.failUnlessEqual(handler_class,
                                 instance.RequestHandlerClass)

    def test_server_has_openid_server(self):
        """ HTTPServer should have an openid_server attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        openid_server = instance.openid_server
        self.failUnless(isinstance(openid_server, Stub_OpenIDServer))

    def test_server_has_auth_service(self):
        """ HTTPServer should have an auth_service attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        auth_service = instance.auth_service
        self.failUnless(auth_service is not None)

    def test_server_has_session_manager(self):
        """ HTTPServer should have a sess_manager attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        sess_manager = instance.sess_manager
        self.failUnless(sess_manager is not None)

    def test_serve_forever_is_callable(self):
        """ HTTPServer.serve_forever should be callable """
        self.failUnless(callable(self.server_class.serve_forever))


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
