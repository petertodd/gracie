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
import urllib

import scaffold
from scaffold import Mock
from test_authservice import Stub_AuthService
from test_httpresponse import Stub_ResponseHeader, Stub_Response

import server
import httpresponse


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


class Stub_Logger(object):
    """ Stub class for Logger """

    def log(self, format, *args, **kwargs):
        """ Log a message """

class Stub_OpenIDServer(object):
    """ Stub class for OpenIDServer """

    def __init__(self):
        """ Set up a new instance """
        self.logger = Stub_Logger()
        self.authservice = Stub_AuthService()
        self._auth_sessions = dict()
        self.create_auth_session("fred")

    def create_auth_session(self, username):
        session_id = "DEADBEEF-%(username)s" % locals()
        self._auth_sessions[session_id] = username
        return session_id

    def get_auth_session(self, session_id):
        return self._auth_sessions[session_id]

    def remove_auth_session(self, session_id):
        del self._auth_sessions[session_id]

class Stub_TCPConnection(object):
    """ Stub class for TCP connection """

    def __init__(self, text):
        """ Set up a new instance """
        self._text = text

    def makefile(self, mode, bufsize):
        """ Make a file handle to the connection stream """
        conn_file = None
        if mode.startswith('r'):
            conn_file = StringIO(self._text)
            conn_file.seek(0)
        elif mode.startswith('w'):
            conn_file = StringIO("")
        return conn_file

class Stub_Request(object):
    """ Stub class for HTTP request encapsulation """

    def __init__(self, method, path,
        version="HTTP/1.1", header=None, data=None,
    ):
        """ Set up a new instance """
        self.method = method
        self.path = path
        self.version = version
        if header is None:
            header = dict()
        self.header = header
        if data is None:
            data = dict()
        self.data = data

    def __str__(self):
        command_text = "%(method)s %(path)s %(version)s" % self.__dict__
        if self.data:
            data_text = urllib.urlencode(self.data)
            self.header['Content-Length'] = len(data_text)
        header_text = "\n".join(["%s: %s" % (name, val)
                                 for name, val in self.header.items()])

        lines = []
        lines.append(command_text)
        if self.header:
            lines.append(header_text)
        lines.append("")
        if self.data:
            lines.append(data_text)

        text = "\n".join(lines)
        return text

    def connection(self):
        """ Return a TCP connection to this request """
        return Stub_TCPConnection(str(self))

class Test_OpenIDRequestHandler(scaffold.TestCase):
    """ Test cases for OpenIDRequestHandler class """

    def setUp(self):
        """ Set up test fixtures """
        self.handler_class = server.OpenIDRequestHandler

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.response_class_prev = server.Response
        self.response_header_class_prev = server.ResponseHeader
        self.page_class_prev = server.pagetemplate.Page
        self.cookie_name_prefix_prev = server.cookie_name_prefix
        server.Response = Mock('Response_class')
        server.Response.mock_returns = Mock('Response')
        server.ResponseHeader = Mock('ResponseHeader_class')
        server.ResponseHeader.mock_returns = Mock('ResponseHeader')
        server.pagetemplate.Page = Mock('Page_class')
        server.pagetemplate.Page.mock_returns = Mock('Page')
        server.cookie_name_prefix = "TEST_"

        self.valid_requests = {
            'get-bogus': dict(
                request = Stub_Request("GET", "/bogus"),
            ),
            'get-root': dict(
                request = Stub_Request("GET", "/"),
            ),
            'no-cookie': dict(
                request = Stub_Request("GET", "/"),
            ),
            'unknown-cookie': dict(
                request = Stub_Request("GET", "/",
                    header = {
                        "Cookie": "TEST_session=DECAFBAD",
                    },
                ),
            ),
            'good-cookie': dict(
                identity_name = "fred",
                request = Stub_Request("GET", "/",
                    header = {
                        "Cookie": "TEST_session=DEADBEEF-fred",
                    },
                ),
            ),
            'id-bogus': dict(
                identity_name = "bogus",
                request = Stub_Request("GET", "/id/bogus"),
            ),
            'id-fred': dict(
                identity_name = "fred",
                request = Stub_Request("GET", "/id/fred"),
            ),
            'logout': dict(
                request = Stub_Request("GET", "/logout"),
            ),
            'login': dict(
                request = Stub_Request("GET", "/login"),
            ),
            'nobutton-login': dict(
                request = Stub_Request("POST", "/login",
                    data = dict(
                        username="bogus",
                        password="bogus",
                    ),
                ),
            ),
            'cancel-login': dict(
                request = Stub_Request("POST", "/login",
                    data = dict(
                        username="bogus",
                        password="bogus",
                        cancel="Cancel",
                    ),
                ),
            ),
            'login-bogus': dict(
                identity_name = "bogus",
                request = Stub_Request("POST", "/login",
                    data = dict(
                        username="bogus",
                        password="bogus",
                        submit="Sign in",
                    ),
                ),
            ),
            'login-fred-wrong': dict(
                identity_name = "fred",
                request = Stub_Request("POST", "/login",
                    data = dict(
                        username="fred",
                        password="password23",
                        submit="Sign in",
                    ),
                ),
            ),
            'login-fred-okay': dict(
                identity_name = "fred",
                request = Stub_Request("POST", "/login",
                    data = dict(
                        username="fred",
                        password="password1",
                        submit="Sign in",
                    ),
                ),
            ),
        }

        logging.basicConfig(stream=self.stdout_test)
        test_logger = logging.getLogger(server.logger_name)

        for key, params in self.valid_requests.items():
            args = params.get('args')
            request = params['request']
            address = params.setdefault('address', ("", 0))
            http_server = params.setdefault('server',
                                            Stub_OpenIDServer())
            http_server.logger = test_logger
            if not args:
                args = dict(
                    request = request.connection(),
                    client_address = address,
                    server = http_server,
                )
            params['args'] = args

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_requests
        )

        version = server.__version__
        self.expect_server_version = "Gracie/%(version)s" % locals()
        python_version = sys.version.split()[0]
        self.expect_sys_version = "Python/%(python_version)s" % locals()

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        server.Response = self.response_class_prev
        server.ResponseHeader = self.response_header_class_prev
        server.pagetemplate.Page = self.page_class_prev
        server.cookie_name_prefix = self.cookie_name_prefix_prev

    def test_instantiate(self):
        """ New OpenIDRequestHandler instance should be created """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            self.failUnless(instance is not None)

    def test_server_as_specified(self):
        """ OpenIDRequestHandler should have specified server attribute """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            http_server = params['server']
            self.failUnlessEqual(http_server, instance.server)

    def test_server_version_as_specified(self):
        """ OpenIDRequestHandler should report module version """
        server_version = self.handler_class.server_version
        self.failUnlessEqual(self.expect_server_version, server_version)

    def test_version_string_as_specified(self):
        """ OpenIDRequestHandler should report expected version string """
        params = self.valid_requests['get-bogus']
        instance = self.handler_class(**params['args'])
        expect_sys_version = self.expect_sys_version
        expect_server_version = self.expect_server_version
        expect_version_string = (
            "%(expect_server_version)s %(expect_sys_version)s"
            % locals() )
        version_string = instance.version_string()
        self.failUnlessEqual(expect_version_string, version_string)

    def test_log_message_to_logger(self):
        """ Request should log messages using server's logger """
        params = self.valid_requests['get-bogus']
        instance = self.handler_class(**params['args'])
        http_server = params['server']
        http_server.logger = Mock("logger")
        http_server.logger.log = Mock("logger.log")
        msg_format = "Foo"
        msg_level = logging.INFO
        msg_args = ("spam", "eggs")
        expect_stdout = """\
            ...
            Called logger.log(%(msg_level)r, %(msg_format)r, ...)
            """ % locals()
        instance.log_message(msg_format, *msg_args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_command_from_request(self):
        """ Request command attribute should come from request text """
        for key, params in self.iterate_params():
            request = params['request']
            instance = self.handler_class(**params['args'])
            self.failUnlessEqual(request.method, instance.command)

    def test_path_from_request(self):
        """ Request path attribute should come from request text """
        for key, params in self.iterate_params():
            request = params['request']
            instance = self.handler_class(**params['args'])
            self.failUnlessEqual(request.path, instance.path)

    def test_request_with_no_cookie_response_not_logged_in(self):
        """ With no session cookie, response should send Not Logged In """
        params = self.valid_requests['no-cookie']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            ...
            Called Response.header.fields.append(
                ('Set-Cookie', 'TEST_session=;Expires=...'))
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_request_with_unknown_cookie_response_not_logged_in(self):
        """ With unknown username, response should send Not Logged In """
        params = self.valid_requests['unknown-cookie']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            ...
            Called Response.header.fields.append(
                ('Set-Cookie', 'TEST_session=;Expires=...'))
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_request_with_good_cookie_response_logged_in(self):
        """ With good session cookie, response should send Logged In """
        params = self.valid_requests['good-cookie']
        identity_name = params['identity_name']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            ...
            Called Response.header.fields.append(
                ('Set-Cookie', 'TEST_session=DEADBEEF-%(identity_name)s'))
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_root_sends_ok_response(self):
        """ Request to GET root document should send OK response """
        params = self.valid_requests['get-root']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_bogus_url_sends_not_found_response(self):
        """ Request to GET unknown URL should send Not Found response """
        params = self.valid_requests['get-bogus']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(404)
            Called Page_class(...)
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_bogus_identity_sends_not_found_response(self):
        """ Request to GET unknown user should send Not Found response """
        params = self.valid_requests['id-bogus']
        identity_name = params['identity_name']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(404)
            Called Page_class(...)
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_known_identity_sends_view_user_response(self):
        """ Request to GET known user should send view user response """
        params = self.valid_requests['id-fred']
        identity_name = params['identity_name']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            Called Page_class('...%(identity_name)s...')
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def get_logout_resets_session_and_redirects(self):
        """ Request to logout should reset session and logout """
        params = self.valid_requests['logout']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(302)
            Called Response.header.fields.append('Location', ...)
            Called Response.header.fields.append(
                ('Set-Cookie', 'TEST_session=;Expires=...'))
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_login_sends_login_form_response(self):
        """ Request to GET login should send login form as response """
        params = self.valid_requests['login']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            Called Page_class(...)
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_post_nobutton_login_sends_not_found_response(self):
        """ POST login with no button should send Not Found response """
        params = self.valid_requests['nobutton-login']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(404)
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_post_login_cancel_sends_cancelled_response(self):
        """ POST login cancel should send cancelled response """
        params = self.valid_requests['cancel-login']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            Called Page_class('Login Cancelled')
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_post_login_bogus_user_sends_failure_response(self):
        """ POST login with bogus user should send failure response """
        params = self.valid_requests['login-bogus']
        identity_name = params['identity_name']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            Called Page_class('Login Failed')
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_post_login_wrong_password_sends_failure_response(self):
        """ POST login with wrong password should send failure response """
        params = self.valid_requests['login-fred-wrong']
        identity_name = params['identity_name']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            Called Page_class('Login Failed')
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_post_login_auth_correct_sends_redirect_response(self):
        """ POST login with correct details should send redirect """
        params = self.valid_requests['login-fred-okay']
        identity_name = params['identity_name']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(302)
            Called ResponseHeader.fields.append(('Location', ...))
            Called Page_class('Login Succeeded')
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )


class Stub_OpenIDRequestHandler(object):
    """ Stub class for OpenIDRequestHandler """

class Test_OpenIDServer(scaffold.TestCase):
    """ Test cases for OpenIDServer class """

    def setUp(self):
        """ Set up test fixtures """

        self.server_class = server.OpenIDServer
        self.stub_handler_class = Stub_OpenIDRequestHandler
        self.mock_handler_class = Mock('OpenIDRequestHandler')

        self.http_server_mock_methods = dict(
            server_bind = Mock('HTTPServer.server_bind'),
        )
        self.http_server_prev_methods = dict()
        for name, value in self.http_server_mock_methods.items():
            self.http_server_prev_methods[name] = getattr(
                server.HTTPServer, name)
            setattr(server.HTTPServer, name, value)

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
        for name, value in self.http_server_prev_methods.items():
            setattr(server.HTTPServer, name, value)

    def test_instantiate(self):
        """ New OpenIDServer instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_logger_name_as_specified(self):
        """ OpenIDServer should have logger of specified name """
        params = self.valid_servers['simple']
        logger_name_prev = server.logger_name
        logger_name_test = "Foo.Bar"
        server.logger_name = logger_name_test
        expect_logger = logging.getLogger(logger_name_test)
        instance = self.server_class(**params['args'])
        self.failUnlessEqual(expect_logger, instance.logger)
        server.logger_name = logger_name_prev

    def test_request_handler_class_as_specified(self):
        """ OpenIDServer should have specified RequestHandlerClass """
        for key, params in self.iterate_params():
            instance = params['instance']
            handler_class = params['handler_class']
            self.failUnlessEqual(handler_class,
                                 instance.RequestHandlerClass)

    def test_create_auth_session_should_return_session_id(self):
        """ Creating an authentication session should return session ID """
        params = self.valid_servers['simple']
        instance = params['instance']
        identity_name = "fred"
        session_id = instance.create_auth_session(identity_name)
        self.failUnless(session_id is not None)

    def test_get_session_unknown_id_raises_keyerror(self):
        """ Getting an unknown session ID should raise KeyError """
        params = self.valid_servers['simple']
        instance = params['instance']
        session_id = "DECAFBAD"
        self.failUnlessRaises(KeyError,
            instance.get_auth_session, session_id
        )

    def test_get_session_returns_same_username(self):
        """ Getting a session by ID should return same username """
        params = self.valid_servers['simple']
        instance = params['instance']
        identity_name = "fred"
        session_id = instance.create_auth_session(identity_name)
        got_name = instance.get_auth_session(session_id)
        self.failUnlessEqual(identity_name, got_name)

    def test_create_session_should_create_unique_id(self):
        """ Creating a session should create unique ID each time """
        params = self.valid_servers['simple']
        instance = params['instance']
        usernames = ["larry", "curly", "moe"]
        sessions = dict()
        for username in usernames:
            session_id = instance.create_auth_session(username)
            self.failIf(session_id in sessions,
                "Session ID %(session_id)r already exists"
                " in %(sessions)r" % locals()
            )

    def test_create_multiple_session_for_same_username(self):
        """ Creating multiple sessions for same username should succeed """
        params = self.valid_servers['simple']
        instance = params['instance']
        usernames = ["larry", "curly", "moe"]
        sessions = dict()
        for username in usernames:
            for _ in range(10):
                session_id = instance.create_auth_session(username)
                sessions[session_id] = username
        for session_id, username in sessions.items():
            got_username = instance.get_auth_session(session_id)
            self.failUnlessEqual(username, got_username)

    def test_remove_session_unknown_should_raise_keyerror(self):
        """ Removing an unknown session ID should raise KeyError """
        params = self.valid_servers['simple']
        instance = params['instance']
        session_id = "DECAFBAD"
        self.failUnlessRaises(KeyError,
            instance.remove_auth_session, session_id
        )

    def test_remove_session_should_cause_get_session_failure(self):
        """ Removing a session should result in failure to get session """
        params = self.valid_servers['simple']
        instance = params['instance']
        identity_name = "fred"
        session_id = instance.create_auth_session(identity_name)
        instance.remove_auth_session(session_id)
        self.failUnlessRaises(KeyError,
            instance.get_auth_session, session_id
        )

    def test_serve_forever_is_callable(self):
        """ OpenIDServer.serve_forever should be callable """
        self.failUnless(callable(self.server_class.serve_forever))


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
