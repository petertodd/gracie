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
import optparse

import scaffold
from scaffold import Mock
from test_authservice import Stub_AuthService
from test_httpresponse import Stub_ResponseHeader, Stub_Response

from gracie import server


class Test_remove_standard_files(scaffold.TestCase):
    """ Test cases for remove_standard_files function """

    def setUp(self):
        """ Set up test fixtures """
        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.server_stdin_prev = server.sys.stdin
        server.sys.stdin = Mock('sys.stdin')
        self.server_stdout_prev = server.sys.stdout
        server.sys.stdout = Mock('sys.stdout')
        self.server_stderr_prev = server.sys.stderr
        server.sys.stderr = Mock('sys.stderr')

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        server.sys.stdin = self.server_stdin_prev
        server.sys.stdout = self.server_stdout_prev
        server.sys.stderr = self.server_stderr_prev


class Mock_fork(object):
    """ Mock callable for os.fork() """

    def __init__(self, name, pids):
        self.mock_name = name
        self._return_pids = iter(pids)

    def _make_message(self, args, kwargs):
        parts = [repr(a) for a in args]
        parts.extend(
            '%s=%r' % (items) for items in sorted(kwargs.items()))
        msg = 'Called %s(%s)' % (self.mock_name, ', '.join(parts))
        if len(msg) > 80:
            msg = 'Called %s(\n    %s)' % (
                self.mock_name, ',\n    '.join(parts))
        return msg

    def __call__(self, *args, **kwargs):
        print self._make_message(args, kwargs)
        return self._return_pids.next()

class Test_become_daemon(scaffold.TestCase):
    """ Test cases for become_daemon function """

    def setUp(self):
        """ Set up test fixtures """
        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.fork_prev = server.os.fork
        test_pids = [23, 0]
        server.os.fork = Mock_fork('os.fork', test_pids)
        self.setsid_prev = server.os.setsid
        server.os.setsid = Mock('os.setsid')
        self._exit_prev = server.os._exit
        server.os._exit = Mock('os._exit')
        self.exit_prev = server.sys.exit
        server.sys.exit = Mock('sys.exit')
        self.remove_files_prev = server.remove_standard_files
        server.remove_standard_files = Mock('remove_standard_files')

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        server.os.fork = self.fork_prev
        server.os.setsid = self.setsid_prev
        server.os._exit = self._exit_prev
        server.sys.exit = self.exit_prev
        server.remove_standard_files = self.remove_files_prev

    def test_parent_exits(self):
        """ become_daemon parent process should exit """
        parent_pid = 0
        server.os.fork = Mock_fork('os.fork', [parent_pid])
        expect_stdout = """\
            Called os.fork()
            Called os._exit(0)
            ...
            """
        server.become_daemon()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_child_starts_new_process_group(self):
        """ become_daemon child should start new process group """
        expect_stdout = """\
            Called os.fork()
            Called os.setsid()
            ...
            """
        server.become_daemon()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_child_forks_next_child_exits(self):
        """ become_daemon should fork, then exit if child """
        test_pids = [23, 42]
        server.os.fork = Mock_fork('os.fork', test_pids)
        expect_stdout = """\
            Called os.fork()
            Called os.setsid()
            Called os.fork()
            Called os._exit(0)
            ...
            """
        server.become_daemon()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_child_forks_next_parent_continues(self):
        """ become_daemon should fork, then continue if parent """
        expect_stdout = """\
            Called os.fork()
            Called os.setsid()
            Called os.fork()
            Called remove_standard_files()
            """
        server.become_daemon()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_removes_standard_files(self):
        """ become_daemon should request removal of standard files """
        expect_stdout = """\
            ...
            Called remove_standard_files()
            """
        server.become_daemon()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )


def stub_server_bind(server):
    """ Stub method to get server location """
    (host, port) = server.server_address
    (server.server_name, server.server_port) = (host, port)

class Stub_HTTPServer(object):
    """ Stub class for HTTPServer """
    def __init__(self,
            server_address, RequestHandlerClass, gracie_server
    ):
        """ Set up a new instance """

    server_bind = stub_server_bind


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

def make_default_opts():
    """ Create commandline opts instance with required values """
    opts = optparse.Values(dict(
        datadir = "/tmp",
        host = "example.org", port = 9779,
    ))
    return opts


class Test_GracieServer(scaffold.TestCase):
    """ Test cases for GracieServer class """

    def setUp(self):
        """ Set up test fixtures """

        self.server_class = server.GracieServer

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.openid_server_prev = server.OpenIDServer
        self.openid_store_prev = server.OpenIDStore
        self.consumer_store_prev = server.ConsumerAuthStore
        server.OpenIDServer = Stub_OpenIDServer
        server.OpenIDStore = Stub_OpenIDStore
        server.ConsumerAuthStore = Stub_ConsumerAuthStore

        self.httpserver_class_prev = server.HTTPServer
        server.HTTPServer = Stub_HTTPServer
        self.handler_class_prev = server.HTTPRequestHandler
        server.RequestHandlerClass = Stub_HTTPRequestHandler
        self.default_port_prev = server.default_port
        server.default_port = 7654

        self.valid_servers = {
            'simple': dict(
            ),
            'with-opts': dict(
                opts = dict(
                    foo="spam",
                    bar="eggs",
                ),
            ),
            'datadir': dict(
                opts = dict(
                    datadir = "/foo/bar",
                ),
                datadir = "/foo/bar",
            ),
        }

        for key, params in self.valid_servers.items():
            args = params.get('args')
            if not args:
                args = dict()
            opts = make_default_opts()
            opts._update_loose(params.get('opts', dict()))
            params['opts'] = opts
            args.update(dict(opts=opts))
            instance = self.server_class(**args)
            params['args'] = args
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_servers
        )

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        server.HTTPServer = self.httpserver_class_prev
        server.HTTPRequestHandler = self.handler_class_prev
        server.default_port = self.default_port_prev
        server.OpenIDServer = self.openid_server_prev
        server.OpenIDStore = self.openid_store_prev
        server.ConsumerAuthStore = self.consumer_store_prev

    def test_instantiate(self):
        """ New GracieServer instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_version_as_specified(self):
        """ GracieServer should have specified version string """
        params = self.valid_servers['simple']
        version_prev = server.__version__
        version_test = "1.414.test"
        server.__version__ = version_test
        instance = self.server_class(**params['args'])
        self.failUnlessEqual(version_test, instance.version)
        server.__version__ = version_prev

    def test_opts_as_specified(self):
        """ GracieServer should have specified opts mapping """
        params = self.valid_servers['with-opts']
        instance = params['instance']
        opts = params['opts']
        self.failUnlessEqual(opts, instance.opts)

    def test_logger_name_as_specified(self):
        """ GracieServer should have logger of specified name """
        params = self.valid_servers['simple']
        logger_name_prev = server.logger_name
        logger_name_test = "Foo.Bar"
        server.logger_name = logger_name_test
        expect_logger = logging.getLogger(logger_name_test)
        instance = self.server_class(**params['args'])
        self.failUnlessEqual(expect_logger, instance.logger)
        server.logger_name = logger_name_prev

    def test_server_creates_http_server(self):
        """ GracieServer should create an HTTP server """
        params = self.valid_servers['simple']
        args = params['args']
        opts = params['opts']
        server_address = (opts.host, opts.port)
        http_server_class_prev = server.HTTPServer
        server.HTTPServer = Mock('HTTPServer_class')
        expect_stdout = """\
            Called HTTPServer_class(
                %(server_address)r,
                <class '...HTTPRequestHandler'>,
                <gracie.server.GracieServer object ...>)
            """ % locals()
        instance = self.server_class(**params['args'])
        server.HTTPServer = http_server_class_prev
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_server_has_openid_server(self):
        """ GracieServer should have an openid_server attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        openid_server = instance.openid_server
        self.failUnless(isinstance(openid_server, Stub_OpenIDServer))

    def test_openid_store_created_with_datadir(self):
        """ OpenIDStore should be created with specified datadir """
        params = self.valid_servers['datadir']
        datadir = params['datadir']
        openid_store_class_prev = server.OpenIDStore
        server.OpenIDStore = Mock('FileOpenIDStore_class')
        expect_stdout = """\
            Called FileOpenIDStore_class(%(datadir)r)
            """ % locals()
        instance = self.server_class(**params['args'])
        server.OpenIDStore = openid_store_class_prev
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_server_has_auth_service(self):
        """ GracieServer should have an auth_service attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        auth_service = instance.auth_service
        self.failUnless(auth_service is not None)

    def test_server_has_session_manager(self):
        """ GracieServer should have a sess_manager attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        sess_manager = instance.sess_manager
        self.failUnless(sess_manager is not None)

    def test_server_has_authorisation_store(self):
        """ GracieServer should have a consumer_auth_store attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        consumer_auth_store = instance.consumer_auth_store
        self.failUnless(consumer_auth_store is not None)

    def test_serve_forever_is_callable(self):
        """ GracieServer.serve_forever should be callable """
        self.failUnless(callable(self.server_class.serve_forever))


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
