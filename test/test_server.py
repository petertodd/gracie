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
from StringIO import StringIO
import optparse

import scaffold
from scaffold import Mock

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
        test_pids = [0, 0]
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
        parent_pid = 23
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

    def test_child_forks_next_parent_exits(self):
        """ become_daemon should fork, then exit if parent """
        test_pids = [0, 42]
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

    def test_child_forks_next_child_continues(self):
        """ become_daemon should fork, then continue if child """
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

class Stub_ResponseHeader(object):
    """ Stub class for response header """

    def __init__(self, code, protocol=None):
        self.code = code
        self.protocol = protocol
        self.fields = dict()

class Stub_Response(object):
    """ Stub class for Response """

    def __init__(self, header, data=None):
        """ Set up a new instance """
        self.header = header
        self.data = data


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


class Stub_SessionManager(object):
    """ Stub class for SessionManager """

    def store_session(self, session):
        pass

    def get_session(self, session_id):
        return None

    def remove_session(self, session_id):
        pass


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
        keys = [
            'identity', 'trust_root', 'immediate', 'return_to',
        ]
        if params is None:
            params = dict()
        for key in keys:
            setattr(self, key, None)
            if key in params:
                setattr(self, key, params[key])

    def answer(self, allow, server_url=None):
        response = Stub_OpenIDResponse(dict(
            allow = allow,
            server_url = server_url,
        ))
        return response

class Stub_OpenIDResponse(object):
    """ Stub class for an OpenID protocol response """

    def __init__(self, params=None):
        self.params = params

    def encodeToURL(self):
        url = "http://stub/openid_response/" + ";".join([
            "%s=%s" % (key, val) for key, val in self.params.items()
        ])
        return url

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
        self.session_manager_prev = server.SessionManager
        server.OpenIDServer = Stub_OpenIDServer
        server.OpenIDStore = Stub_OpenIDStore
        server.ConsumerAuthStore = Stub_ConsumerAuthStore
        server.SessionManager = Stub_SessionManager

        self.httpserver_class_prev = server.HTTPServer
        server.HTTPServer = Stub_HTTPServer
        self.handler_class_prev = server.HTTPRequestHandler
        server.RequestHandlerClass = Stub_HTTPRequestHandler

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
            args.update(dict(
                socket_params=None,
                opts=opts,
            ))
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
        server.OpenIDServer = self.openid_server_prev
        server.OpenIDStore = self.openid_store_prev
        server.ConsumerAuthStore = self.consumer_store_prev
        server.SessionManager = self.session_manager_prev

    def test_instantiate(self):
        """ New GracieServer instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failIfIs(None, instance)

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
        self.failIfIs(None, auth_service)

    def test_server_has_session_manager(self):
        """ GracieServer should have a sess_manager attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        sess_manager = instance.sess_manager
        self.failIfIs(None, sess_manager)

    def test_server_has_authorisation_store(self):
        """ GracieServer should have a consumer_auth_store attribute """
        params = self.valid_servers['simple']
        instance = params['instance']
        consumer_auth_store = instance.consumer_auth_store
        self.failIfIs(None, consumer_auth_store)

    def test_serve_forever_is_callable(self):
        """ GracieServer.serve_forever should be callable """
        self.failUnless(callable(self.server_class.serve_forever))


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
