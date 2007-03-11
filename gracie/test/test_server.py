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
        session_id = instance.create_session()
        self.failUnless(session_id is not None)

    def test_get_session_unknown_id_raises_keyerror(self):
        """ Getting an unknown session ID should raise KeyError """
        instance = self.manager_class()
        session_id = "DECAFBAD"
        self.failUnlessRaises(KeyError,
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
            self.failIf(session_id in sessions,
                "Session ID %(session_id)r already exists"
                " in %(sessions)r" % locals()
            )
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
        self.failUnlessRaises(KeyError,
            instance.remove_session, session_id
        )

    def test_remove_session_should_cause_get_session_failure(self):
        """ Removing a session should result in failure to get session """
        instance = self.manager_class()
        identity_name = "fred"
        session_id = instance.create_session()
        instance.remove_session(session_id)
        self.failUnlessRaises(KeyError,
            instance.get_session, session_id
        )


class Stub_ConsumerAuthStore(object):
    """ Stub class for ConsumerAuthStore """

    def __init__(self):
        self._authorisations = dict()

    def store_authorisation(self, auth_tuple, status):
        self._authorisations[auth_tuple] = status

    def is_authorised(self, auth_tuple):
        return self._authorisations.get(auth_tuple, False)

class Stub_ConsumerAuthStore_always_auth(Stub_ConsumerAuthStore):
    """ ConsumerAuthStore stub that always authorises """

    def is_authorised(self, auth_tuple):
        return True

class Stub_ConsumerAuthStore_never_auth(Stub_ConsumerAuthStore):
    """ ConsumerAuthStore stub that never authorises """

    def is_authorised(self, auth_tuple):
        return False


class Test_ConsumerAuthStore(scaffold.TestCase):
    """ Test cases for ConsumerAuthStore class """

    def setUp(self):
        """ Set up test fixtures """

        self.store_class = server.ConsumerAuthStore

    def test_instantiate(self):
        """ New ConsumerAuthStore instance should be created """
        instance = self.store_class()
        self.failUnless(instance is not None)

    def test_is_authorised_unknown_returns_false(self):
        """ is_authorised for unknown args should return False """
        instance = self.store_class()
        auth_tuple = ("bogus", "bogus")
        is_authorised = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(False, is_authorised)

    def test_store_authorisation_result_in_authorisation(self):
        """ store_authorisation should let is_authorised succeed """
        instance = self.store_class()
        identity = "/id/fred"
        trust_root = "http://example.com/"
        auth_tuple = (identity, trust_root)
        status = True
        instance.store_authorisation(auth_tuple, status)
        got_status = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(True, got_status)

    def test_remove_authorisation_unknown_should_succeed(self):
        """ remove_authorisation for unknown args should succeed """
        instance = self.store_class()
        auth_tuple = ("bogus", "bogus")
        instance.remove_authorisation(auth_tuple)
        is_authorised = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(False, is_authorised)

    def test_remove_authorisation_result_in_no_authorisation(self):
        """ remove_authorisation should make is_authorised return False """
        instance = self.store_class()
        identity = "/id/fred"
        trust_root = "http://example.com/"
        auth_tuple = (identity, trust_root)
        status = True
        instance.store_authorisation(auth_tuple, status)
        instance.remove_authorisation(auth_tuple)
        got_status = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(False, got_status)


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

    def decodeRequest(self, request):
        return Stub_OpenIDResponse()

    def encodeResponse(self, response):
        return Stub_OpenIDWebResponse()

class Stub_OpenIDRequest(object):
    """ Stub class for an OpenID protocol request """

    def __init__(self, http_query, params=None):
        """ Set up a new instance """

        self.mode = http_query.get('openid.mode')
        keys = ('identity', 'trust_root', 'immediate')
        if params is None:
            params = dict()
        for key in keys:
            setattr(self, key, None)
            if key in params:
                setattr(self, key, params[key])

    def answer(self, *args, **kwargs):
        return Stub_OpenIDResponse()

class Stub_OpenIDResponse(object):
    """ Stub class for an OpenID protocol response """

class Stub_OpenIDWebResponse(object):
    """ Stub class for an encoded OpenID response """

    def __init__(self):
        """ Set up a new instance """
        self.code = 200
        self.headers = {"openid": "yes"}
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
        self.consumer_store_prev = server.ConsumerAuthStore
        server.OpenIDServer = Stub_OpenIDServer
        server.OpenIDStore = Stub_OpenIDStore
        server.ConsumerAuthStore = Stub_ConsumerAuthStore

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
        server.ConsumerAuthStore = self.consumer_store_prev
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

    def test_server_has_authorisation_store(self):
        """ HTTPServer should have a consumer_auth_store attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        consumer_auth_store = instance.consumer_auth_store
        self.failUnless(consumer_auth_store is not None)

    def test_serve_forever_is_callable(self):
        """ HTTPServer.serve_forever should be callable """
        self.failUnless(callable(self.server_class.serve_forever))


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
