#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test_httprequest.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for httprequest module
"""

import sys
from StringIO import StringIO
import logging
import urllib

import scaffold
from scaffold import Mock
from test_authservice import Stub_AuthService
from test_httpresponse import Stub_ResponseHeader, Stub_Response
from test_server import (
    Stub_OpenIDStore, Stub_OpenIDServer, Stub_OpenIDError,
    Stub_OpenIDRequest, Stub_OpenIDResponse, Stub_OpenIDWebResponse,
    Stub_ConsumerAuthStore,
    Stub_ConsumerAuthStore_always_auth,
    Stub_ConsumerAuthStore_never_auth,
)

from gracie import httprequest


class Stub_Logger(object):
    """ Stub class for Logger """

    def log(self, format, *args, **kwargs):
        """ Log a message """

    error = log
    warn = log
    info = log
    debug = log

class Stub_SessionManager(object):
    """ Stub class for SessionManager """

    def __init__(self):
        """ Set up a new instance """
        self._sessions = dict()
        self.create_session(dict(
            username="fred",
        ))

    def create_session(self, session):
        session_id = "DEADBEEF-%(username)s" % session
        session.update(dict(session_id = session_id))
        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id):
        return self._sessions[session_id]

    def remove_session(self, session_id):
        del self._sessions[session_id]

class Stub_HTTPServer(object):
    """ Stub class for HTTPServer """

    def __init__(self, server_address, handler_class, gracie_server):
        """ Set up a new instance """
        self.gracie_server = gracie_server
        (host, port) = server_address
        self.server_location = "%(host)s:%(port)s" % locals()

class Stub_HTTPRequestHandler(object):
    """ Stub class for HTTPRequestHandler """

class Stub_GracieServer(object):
    """ Stub class for GracieServer """

    version = "3.14.test"

    def __init__(self, server_address):
        """ Set up a new instance """
        self.logger = Stub_Logger()
        self.server_location = "%s:%s" % server_address
        self.http_server = Stub_HTTPServer(
            server_address, Stub_HTTPRequestHandler(), self
        )
        store = Stub_OpenIDStore(None)
        self.openid_server = Stub_OpenIDServer(store)
        self.auth_service = Stub_AuthService()
        self.sess_manager = Stub_SessionManager()
        self.consumer_auth_store = Stub_ConsumerAuthStore()


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
        version="HTTP/1.1", header=None, query=None,
    ):
        """ Set up a new instance """
        self.method = method.upper()
        self.path = path
        self.version = version
        if header is None:
            header = []
        self.header = header
        if query is None:
            query = dict()
        self.query = query
        self.data = ""

    def _encode_query(self):
        if self.query:
            query_text = urllib.urlencode(self.query)

            if self.method in ["POST", "PUT"]:
                self.header.append(
                    ("Content-Length", str(len(query_text)))
                )
                self.data += query_text
            elif self.method in ["GET", "HEAD"]:
                path = self.path
                self.path = "%(path)s?%(query_text)s" % locals()

    def __str__(self):
        self._encode_query()
        command_text = "%(method)s %(path)s %(version)s" % self.__dict__
        header_text = "\n".join(["%s: %s" % (name, val)
                                 for name, val in self.header])

        lines = []
        lines.append(command_text)
        if header_text:
            lines.append(header_text)
        lines.append("")
        if self.data:
            lines.append(self.data)

        text = "\n".join(lines)
        return text

    def connection(self):
        """ Return a TCP connection to this request """
        return Stub_TCPConnection(str(self))


class Test_HTTPRequestHandler(scaffold.TestCase):
    """ Test cases for HTTPRequestHandler class """

    def setUp(self):
        """ Set up test fixtures """
        self.handler_class = httprequest.HTTPRequestHandler

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.response_class_prev = httprequest.Response
        self.response_header_class_prev = httprequest.ResponseHeader
        self.page_class_prev = httprequest.pagetemplate.Page
        self.cookie_name_prev = httprequest.session_cookie_name
        self.dispatch_method_prev = self.handler_class._dispatch
        httprequest.Response = Mock('Response_class')
        httprequest.Response.mock_returns = Mock('Response')
        httprequest.ResponseHeader = Mock('ResponseHeader_class')
        httprequest.ResponseHeader.mock_returns = Mock('ResponseHeader')
        httprequest.pagetemplate.Page = Mock('Page_class')
        httprequest.pagetemplate.Page.mock_returns = Mock('Page')
        httprequest.session_cookie_name = "TEST_session"
        mock_openid_server = Mock('openid_server')

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
                    header = [
                        ("Cookie", "TEST_session=DECAFBAD"),
                    ],
                ),
            ),
            'good-cookie': dict(
                identity_name = "fred",
                request = Stub_Request("GET", "/",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-fred"),
                    ],
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
                    query = dict(
                        username="bogus",
                        password="bogus",
                    ),
                ),
            ),
            'cancel-login': dict(
                request = Stub_Request("POST", "/login",
                    query = dict(
                        username="bogus",
                        password="bogus",
                        cancel="Cancel",
                    ),
                ),
            ),
            'login-bogus': dict(
                identity_name = "bogus",
                request = Stub_Request("POST", "/login",
                    query = dict(
                        username="bogus",
                        password="bogus",
                        submit="Sign in",
                    ),
                ),
            ),
            'login-fred-wrong': dict(
                identity_name = "fred",
                request = Stub_Request("POST", "/login",
                    query = dict(
                        username="fred",
                        password="password23",
                        submit="Sign in",
                    ),
                ),
            ),
            'login-fred-okay': dict(
                identity_name = "fred",
                request = Stub_Request("POST", "/login",
                    query = dict(
                        username="fred",
                        password="password1",
                        submit="Sign in",
                    ),
                ),
            ),
            'openid-no-query': dict(
                request = Stub_Request("GET", "/openidserver"),
            ),
            'openid-bogus-query': dict(
                request = Stub_Request("GET", "/openidserver",
                    query = {
                        "foo.bar": "spam",
                        "flim.flam": "",
                        "wibble.wobble": "eggs",
                    },
                ),
            ),
            'openid-query-associate': dict(
                request = Stub_Request("GET", "/openidserver",
                    query = {
                        "openid.mode": "associate",
                        "openid.session_type": "",
                    },
                ),
            ),
            'openid-query-checkid_immediate-no-session': dict(
                request = Stub_Request("GET", "/openidserver",
                    header = [],
                    query = {
                        "openid.mode": "checkid_immediate",
                        "openid.identity": "http://example.org:0/id/fred",
                        "openid.return_to": "http://example.com/",
                    },
                ),
            ),
            'openid-query-checkid_setup-no-session': dict(
                request = Stub_Request("GET", "/openidserver",
                    header = [],
                    query = {
                        "openid.mode": "checkid_setup",
                        "openid.identity": "http://example.org:0/id/fred",
                        "openid.return_to": "http://example.com/",
                    },
                ),
            ),
            'openid-query-checkid_immediate-other-session': dict(
                request = Stub_Request("GET", "/openidserver",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-bill"),
                    ],
                    query = {
                        "openid.mode": "checkid_immediate",
                        "openid.identity": "http://example.org:0/id/fred",
                        "openid.return_to": "http://example.com/",
                    },
                ),
            ),
            'openid-query-checkid_setup-other-session': dict(
                request = Stub_Request("GET", "/openidserver",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-bill"),
                    ],
                    query = {
                        "openid.mode": "checkid_setup",
                        "openid.identity": "http://example.org:0/id/fred",
                        "openid.return_to": "http://example.com/",
                    },
                ),
            ),
            'openid-query-checkid_immediate-right-session': dict(
                request = Stub_Request("GET", "/openidserver",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-fred"),
                    ],
                    query = {
                        "openid.mode": "checkid_immediate",
                        "openid.identity": "http://example.org:0/id/fred",
                        "openid.return_to": "http://example.com/",
                    },
                ),
            ),
            'openid-query-checkid_setup-right-session': dict(
                request = Stub_Request("GET", "/openidserver",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-fred"),
                    ],
                    query = {
                        "openid.mode": "checkid_setup",
                        "openid.identity": "http://example.org:0/id/fred",
                        "openid.return_to": "http://example.com/",
                    },
                ),
            ),
            'get-authorise': dict(
                request = Stub_Request("GET", "/authorise",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-fred"),
                    ],
                    query = {
                        "trust_root": "http://example.com/",
                        "identity": "http://example.org:0/id/fred",
                        "return_to": "http://www.example.com/",
                        "submit_deny": "Deny",
                    },
                ),
            ),
            'post-authorise-no-session': dict(
                request = Stub_Request("POST", "/authorise",
                    header = [],
                    query = {
                        "trust_root": "http://example.com/",
                        "identity": "http://example.org:0/id/fred",
                        "return_to": "http://www.example.com/",
                        "submit_approve": "Approve",
                    },
                ),
            ),
            'post-authorise-other-session': dict(
                request = Stub_Request("POST", "/authorise",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-bill"),
                    ],
                    query = {
                        "trust_root": "http://example.com/",
                        "identity": "http://example.org:0/id/fred",
                        "return_to": "http://www.example.com/",
                        "submit_approve": "Approve",
                    },
                ),
            ),
            'post-authorise-approve': dict(
                request = Stub_Request("POST", "/authorise",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-fred"),
                    ],
                    query = {
                        "trust_root": "http://example.com/",
                        "identity": "http://example.org:0/id/fred",
                        "return_to": "http://www.example.com/",
                        "submit_approve": "Approve",
                    },
                ),
                auth_tuple = (
                    "http://example.org:0/id/fred",
                    "http://example.com/"
                ),
                auth_status = True,
            ),
            'post-authorise-deny': dict(
                request = Stub_Request("POST", "/authorise",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-fred"),
                    ],
                    query = {
                        "trust_root": "http://example.com/",
                        "identity": "http://example.org:0/id/fred",
                        "return_to": "http://www.example.com/",
                        "submit_deny": "Deny",
                    },
                ),
                auth_tuple = (
                    "http://example.org:0/id/fred",
                    "http://example.com/"
                ),
                auth_status = False,
            ),
        }

        logging.basicConfig(stream=self.stdout_test)

        for key, params in self.valid_requests.items():
            args = params.get('args')
            request = params['request']
            address = params.setdefault('address',
                ("example.org", 0))
            gracie_server = Stub_GracieServer(address)
            server = params.setdefault('server',
                gracie_server.http_server
            )
            mock_openid_request = self._make_mock_openid_request(
                request.query
            )
            mock_openid_server = self._make_mock_openid_server(
                mock_openid_request
            )
            server.gracie_server.openid_server = mock_openid_server
            if not args:
                args = dict(
                    request = request.connection(),
                    client_address = address,
                    server = server,
                )
            params['args'] = args

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_requests
        )

        version = Stub_GracieServer.version
        self.expect_server_version = "Gracie/%(version)s" % locals()
        python_version = sys.version.split()[0]
        self.expect_sys_version = "Python/%(python_version)s" % locals()

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        httprequest.Response = self.response_class_prev
        httprequest.ResponseHeader = self.response_header_class_prev
        httprequest.pagetemplate.Page = self.page_class_prev
        httprequest.session_cookie_name = self.cookie_name_prev
        self.handler_class._dispatch = self.dispatch_method_prev

    def _make_mock_openid_request(self, http_query):
        """ Make a mock OpenIDRequest for a given HTTP query """
        openid_request = Mock('OpenIDRequest')
        keys = ('mode', 'identity', 'trust_root', 'return_to')
        query_key_prefix = 'openid.'
        for key in keys:
            query_key = '%(query_key_prefix)s%(key)s' % locals()
            setattr(openid_request, key, http_query.get(query_key))
        openid_request.immediate = (
            openid_request.mode in ['checkid_immediate']
        )
        openid_request.answer.mock_returns = Stub_OpenIDResponse()

        return openid_request

    def _make_mock_openid_server(self, openid_request):
        """ Make a mock OpenIDServer for a given HTTP query """
        openid_server = Mock('openid_server')

        if openid_request.mode:
            openid_server.decodeRequest.mock_returns = \
                openid_request
            openid_server.handleRequest.mock_returns = \
                Stub_OpenIDResponse()
            openid_server.encodeResponse.mock_returns = \
                Stub_OpenIDWebResponse()

        return openid_server

    def test_instantiate(self):
        """ New HTTPRequestHandler instance should be created """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            self.failUnless(instance is not None)

    def test_server_as_specified(self):
        """ HTTPRequestHandler should have specified server attribute """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            server = params['server']
            self.failUnlessEqual(server, instance.server)

    def test_server_version_as_specified(self):
        """ HTTPRequestHandler should report module version """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            self.failUnlessEqual(
                self.expect_server_version, instance.server_version
            )

    def test_version_string_as_specified(self):
        """ HTTPRequestHandler should report expected version string """
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
        server = params['server']
        server.gracie_server.logger = Mock("logger")
        server.gracie_server.logger.log = Mock("logger.log")
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

    def test_internal_error_sends_server_error_response(self):
        """ When an error condition is raised, should send Server Error """
        class TestingError(StandardError):
            pass
        def raise_Error(_):
            raise TestingError("Testing error")
        self.handler_class._dispatch = raise_Error

        params = self.valid_requests['get-root']
        try:
            instance = self.handler_class(**params['args'])
        except TestingError:
            pass
        expect_stdout = """\
            Called ResponseHeader_class(500)
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

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
            Called Page_class('...')
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
            Called Page_class('...')
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
            Called Page_class('...')
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
            Called Page_class('Login')
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
            Called ResponseHeader.fields.append(('Location', '...'))
            ...
            Called Response.send_to_handler(
                ...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_server_no_query_sends_about_site_response(self):
        """ GET to server without query should send About page """
        params = self.valid_requests['openid-no-query']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called openid_server.decodeRequest(...)
            Called ResponseHeader_class(200)
            Called Page_class('About this site')
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_server_bogus_query_sends_server_error_response(self):
        """ GET to server with bogus query should send Server Error """
        def raise_ProtocolError(_):
            raise Stub_OpenIDError("Testing error")

        params = self.valid_requests['openid-bogus-query']
        args = params['args']
        server = args['server']
        server.gracie_server.openid_server.decodeRequest = \
            raise_ProtocolError
        try:
            instance = self.handler_class(**args)
        except Stub_OpenIDError:
            pass
        expect_stdout = """\
            Called ResponseHeader_class(500)
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_get_server_assoc_query_delegates_to_openid(self):
        """ OpenID associate query should be passed to openid server """
        params = self.valid_requests['openid-query-associate']
        args = params['args']
        server = args['server']
        instance = self.handler_class(**args)
        expect_stdout = """\
            Called openid_server.decodeRequest(...)
            Called openid_server.handleRequest(...)
            Called openid_server.encodeResponse(...)
            Called ResponseHeader_class(200)
            Called ResponseHeader.fields.append(('openid', 'yes'))
            Called Response_class(..., 'OpenID response')
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_checkid_immediate_no_session_returns_failure(self):
        """ OpenID check_immediate with no session should reject """
        params_key = 'openid-query-checkid_immediate-no-session'
        params = self.valid_requests[params_key]
        args = params['args']
        server = args['server']
        server.gracie_server.consumer_auth_store = \
            Stub_ConsumerAuthStore_always_auth()
        instance = self.handler_class(**args)
        expect_stdout = """\
            Called openid_server.decodeRequest(...)
            Called OpenIDRequest.answer(False, ...)
            Called openid_server.encodeResponse(...)
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_checkid_setup_wrong_session_returns_login_page(self):
        """ OpenID checkid_setup with wrong session should request login """
        for params_key in [
            'openid-query-checkid_setup-no-session',
            'openid-query-checkid_setup-other-session',
        ]:
            params = self.valid_requests[params_key]
            args = params['args']
            server = args['server']
            server.gracie_server.consumer_auth_store = \
                Stub_ConsumerAuthStore_always_auth()
            instance = self.handler_class(**args)
            expect_stdout = """\
                Called openid_server.decodeRequest(...)
                Called ResponseHeader_class(200)
                Called Page_class('Wrong Authorisation')
                ...
                Called Response.send_to_handler(...)
                """
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
            )

    def test_checkid_immediate_no_auth_returns_failure(self):
        """ OpenID checkid_immediate with no auth should return False """
        params_key = 'openid-query-checkid_immediate-right-session'
        params = self.valid_requests[params_key]
        args = params['args']
        server = args['server']
        server.gracie_server.consumer_auth_store = \
            Stub_ConsumerAuthStore_never_auth()
        instance = self.handler_class(**args)
        expect_stdout = """\
            Called openid_server.decodeRequest(...)
            Called OpenIDRequest.answer(False, ...)
            Called openid_server.encodeResponse(...)
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_checkid_setup_no_auth_sends_authorise_query_page(self):
        """ OpenID checkid_setup with no auth should send Authorise? """
        params_key = 'openid-query-checkid_setup-right-session'
        params = self.valid_requests[params_key]
        args = params['args']
        server = args['server']
        server.gracie_server.consumer_auth_store = \
            Stub_ConsumerAuthStore_never_auth()
        instance = self.handler_class(**args)
        expect_stdout = """\
            Called openid_server.decodeRequest(...)
            Called ResponseHeader_class(200)
            Called Page_class('Approve OpenID Request?')
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_checkid_with_session_and_auth_returns_success(self):
        """ OpenID checkid with right session and auth should succeed """
        for params_key in [
            'openid-query-checkid_immediate-right-session',
            'openid-query-checkid_setup-right-session',
        ]:
            params = self.valid_requests[params_key]
            args = params['args']
            server = args['server']
            server.gracie_server.consumer_auth_store = \
                Stub_ConsumerAuthStore_always_auth()
            instance = self.handler_class(**args)
            expect_stdout = """\
                Called openid_server.decodeRequest(...)
                Called OpenIDRequest.answer(True)
                Called openid_server.encodeResponse(...)
                ...
                Called Response.send_to_handler(...)
                """
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
            )

    def test_get_authorise_returns_not_found_response(self):
        """ GET authorise should return Not Found response """
        params = self.valid_requests['get-authorise']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(404)
            Called Page_class('...')
            ...
            Called Response.send_to_handler(...)
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_post_authorise_wrong_session_returns_login_page(self):
        """ POST authorise with wrong session should request login """
        for params_key in [
            'post-authorise-no-session',
            'post-authorise-other-session',
        ]:
            params = self.valid_requests[params_key]
            args = params['args']
            instance = self.handler_class(**args)
            expect_stdout = """\
                Called ResponseHeader_class(200)
                Called Page_class('Wrong Authorisation')
                ...
                Called Response.send_to_handler(...)
                """
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
            )

    def test_post_authorise_with_right_session_stores_result(self):
        """ POST authorise with right session should store result """
        for params_key in [
            'post-authorise-approve',
            'post-authorise-deny',
        ]:
            params = self.valid_requests[params_key]
            args = params['args']
            server = args['server']
            checkid_request = self.valid_requests[
                'openid-query-checkid_setup-right-session']['request']
            session = server.gracie_server.sess_manager.get_session(
                "DEADBEEF-fred"
            )
            openid_request = self._make_mock_openid_request(
                http_query = checkid_request.query
            )
            session['last_openid_request'] = openid_request
            mock_openid_server = self._make_mock_openid_server(
                openid_request
            )
            server.gracie_server.openid_server = mock_openid_server
            mock_auth_store = Mock('ConsumerAuthStore')
            server.gracie_server.consumer_auth_store = mock_auth_store
            auth_tuple = params['auth_tuple']
            auth_status = params['auth_status']
            instance = self.handler_class(**args)
            expect_stdout = """\
                Called ConsumerAuthStore.store_authorisation(
                    %(auth_tuple)r,
                    %(auth_status)r)
                Called OpenIDRequest.answer(%(auth_status)r)
                Called openid_server.encodeResponse(...)
                ...
                Called Response.send_to_handler(...)
                """ % locals()
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
            )
            self.stdout_test.truncate(0)


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
