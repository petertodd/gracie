#! /usr/bin/python
# -*- coding: utf-8 -*-

# test/test_httprequest.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben@benfinney.id.au>
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
from test_server import (
    Stub_OpenIDStore, Stub_OpenIDServer, Stub_OpenIDError,
    Stub_OpenIDRequest, Stub_OpenIDResponse, Stub_OpenIDWebResponse,
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

    def create_session(self, session):
        username = session.get('username')
        session_id = session.get('session_id')
        if session_id is None:
            if username is None:
                session_id = "DEADBEEF"
            else:
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
        self.server_location = "%(host)s:%(port)s" % vars()

class Stub_HTTPRequestHandler(object):
    """ Stub class for HTTPRequestHandler """

class Stub_OptionValues(object):
    """ Stub class for optparse.OptionValues """

    def __init__(self, opt_dict):
        """ Set up a new instance """
        for key, value in opt_dict.items():
            setattr(self, key, value)

class Stub_GracieServer(object):
    """ Stub class for GracieServer """

    version = "3.14.test"

    def __init__(self, opts):
        """ Set up a new instance """
        self.opts = opts
        server_address = (opts.host, opts.port)
        self.server_location = "%s:%s" % server_address
        self.http_server = Stub_HTTPServer(
            server_address, Stub_HTTPRequestHandler(), self
            )
        store = Stub_OpenIDStore(None)
        self.openid_server = Stub_OpenIDServer(store)
        self.auth_service = Stub_AuthService()
        self.sess_manager = Stub_SessionManager()


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

    def __init__(
        self, method, path,
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
                self.path = "%(path)s?%(query_text)s" % vars()

    def __str__(self):
        self._encode_query()
        command_text = "%(method)s %(path)s %(version)s" % vars(self)
        header_text = "\n".join(
            "%s: %s" % (name, val)
            for name, val in self.header)

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
                session_id = "DECAFBAD",
                ),
            'good-cookie': dict(
                identity_name = "fred",
                request = Stub_Request("GET", "/",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF-fred"),
                        ],
                    ),
                session = dict(
                    session_id = "DEADBEEF-fred",
                    username = "fred",
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
                session = dict(
                    session_id = "DEADBEEF-bill",
                    username = "bill",
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
                session = dict(
                    session_id = "DEADBEEF-bill",
                    username = "bill",
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
                session = dict(
                    session_id = "DEADBEEF-fred",
                    username = "fred",
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
                session = dict(
                    session_id = "DEADBEEF-fred",
                    username = "fred",
                    ),
                ),
            'openid-cancel-login': dict(
                request = Stub_Request("POST", "/login",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF"),
                        ],
                    query = dict(
                        username = "bogus",
                        password = "bogus",
                        cancel = "Cancel",
                        ),
                    ),
                session = dict(
                    session_id = "DEADBEEF",
                    last_openid_request = Stub_OpenIDRequest(
                        http_query = {'openid.mode': "checkid_setup"},
                        params = dict(
                            identity = "http://example.org:0/id/fred",
                            trust_root = "http://example.com/",
                            return_to = "http://example.com/account",
                            ),
                        ),
                    ),
                ),
            'openid-login-bill-other': dict(
                identity_name = "fred",
                request = Stub_Request("POST", "/login",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF"),
                        ],
                    query = dict(
                        username="bill",
                        password="secret1",
                        submit="Sign in",
                        ),
                    ),
                session = dict(
                    session_id = "DEADBEEF",
                    last_openid_request = Stub_OpenIDRequest(
                        http_query = {'openid.mode': "checkid_setup"},
                        params = dict(
                            identity = "http://example.org:0/id/fred",
                            trust_root = "http://example.com/",
                            return_to = "http://example.com/account",
                            ),
                        ),
                    ),
                ),
            'openid-login-fred-okay': dict(
                identity_name = "fred",
                request = Stub_Request("POST", "/login",
                    header = [
                        ("Cookie", "TEST_session=DEADBEEF"),
                        ],
                    query = dict(
                        username="fred",
                        password="password1",
                        submit="Sign in",
                        ),
                    ),
                session = dict(
                    session_id = "DEADBEEF",
                    last_openid_request = Stub_OpenIDRequest(
                        http_query = {'openid.mode': "checkid_setup"},
                        params = dict(
                            identity = "http://example.org:0/id/fred",
                            trust_root = "http://example.com/",
                            return_to = "http://example.com/account",
                            ),
                        ),
                    ),
                ),
            }

        logging.basicConfig(stream=self.stdout_test)

        for key, params in self.valid_requests.items():
            args = params.get('args')
            request = params['request']
            opts = Stub_OptionValues(dict(
                host = "example.org",
                port = 0,
                root_url = "http://example.org:0/",
                ))
            gracie_server = Stub_GracieServer(opts)
            sess_manager = gracie_server.sess_manager
            session = params.get('session', dict())
            sess_manager.create_session(session)
            server = params.setdefault(
                'server',
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
                    client_address = (opts.host, opts.port),
                    server = server,
                    )
            params['args'] = args

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_requests
            )

        version = Stub_GracieServer.version
        self.expect_server_version = "Gracie/%(version)s" % vars()
        python_version = sys.version.split()[0]
        self.expect_sys_version = "Python/%(python_version)s" % vars()

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
            query_key = '%(query_key_prefix)s%(key)s' % vars()
            setattr(openid_request, key, http_query.get(query_key))
        openid_request.immediate = (
            openid_request.mode in ['checkid_immediate']
            )
        openid_request.answer.mock_returns = Stub_OpenIDResponse()

        return openid_request

    def _make_mock_openid_server(self, openid_request):
        """ Make a mock OpenIDServer for a given HTTP query """
        def stub_sign(obj):
            return obj

        openid_server = Mock('openid_server')

        if openid_request.mode:
            openid_server.decodeRequest.mock_returns = \
                openid_request
            openid_server.handleRequest.mock_returns = \
                Stub_OpenIDResponse()
            openid_server.encodeResponse.mock_returns = \
                Stub_OpenIDWebResponse()
        openid_server.signatory.sign = stub_sign

        return openid_server

    def test_instantiate(self):
        """ New HTTPRequestHandler instance should be created """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            self.failIfIs(None, instance)

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
            ) % vars()
        version_string = instance.version_string()
        self.failUnlessEqual(expect_version_string, version_string)

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

    def test_request_with_no_cookie_response_creates_session(self):
        """ With no session cookie, response should create new session """
        params = self.valid_requests['no-cookie']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            ...
            Called Response.header.fields.append(
                ('Set-Cookie', 'TEST_session=DEADBEEF'))
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_request_with_unknown_cookie_creates_new_session(self):
        """ With unknown username, response should create new session """
        params = self.valid_requests['unknown-cookie']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            ...
            Called Response.header.fields.append(
                ('Set-Cookie', 'TEST_session=DEADBEEF'))
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
            """ % vars()
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
            """ % vars()
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
            """ % vars()
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
            """ % vars()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def get_logout_creates_new_session_and_redirects(self):
        """ Request to logout should create new session and logout """
        params = self.valid_requests['logout']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(302)
            Called Response.header.fields.append('Location', ...)
            Called Response.header.fields.append(
                ('Set-Cookie', 'TEST_session=DEADBEEF'))
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
            """ % vars()
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
            """ % vars()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_post_login_cancel_no_openid_redirects_to_root(self):
        """ Login cancel with no OpenID should redirect to root """
        params = self.valid_requests['cancel-login']
        instance = self.handler_class(**params['args'])
        root_url = params['server'].gracie_server.opts.root_url
        expect_stdout = """\
            Called ResponseHeader_class(302)
            Called ResponseHeader.fields.append(('Location', %(root_url)r))
            ...
            Called Response.send_to_handler(...)
            """ % vars()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_post_openid_login_cancel_redirects_to_openid_url(self):
        """ Login cancel with OpenID should redirect to OpenID URL """
        params = self.valid_requests['openid-cancel-login']
        openid_request = params['session']['last_openid_request']
        instance = self.handler_class(**params['args'])
        return_url = openid_request.answer(False).encodeToURL()
        expect_stdout = """\
            Called ResponseHeader_class(302)
            Called ResponseHeader.fields.append(
                ('Location', %(return_url)r))
            ...
            Called Response.send_to_handler(...)
            """ % vars()
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
            """ % vars()
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
            """ % vars()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_post_login_auth_correct_no_openid_redirects_to_root(self):
        """ Login with no OpenID, correct details should redirect to root """
        params = self.valid_requests['login-fred-okay']
        identity_name = params['identity_name']
        root_url = params['server'].gracie_server.opts.root_url
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(302)
            Called ResponseHeader.fields.append(('Location', %(root_url)r))
            ...
            Called Response.send_to_handler(
                ...)
            """ % vars()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_post_openid_login_auth_correct_redirects_to_openid_url(self):
        """ Login correct with OpenID should redirect to OpenID URL """
        params = self.valid_requests['openid-login-fred-okay']
        openid_request = params['session']['last_openid_request']
        instance = self.handler_class(**params['args'])
        return_url = openid_request.answer(True).encodeToURL()
        expect_stdout = """\
            Called ResponseHeader_class(302)
            Called ResponseHeader.fields.append(
                ('Location', %(return_url)r))
            ...
            Called Response.send_to_handler(...)
            """ % vars()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_post_openid_login_auth_other_sends_wrong_auth(self):
        """ Login wrong auth with OpenID should send Auth Required """
        params = self.valid_requests['openid-login-bill-other']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(200)
            Called Page_class('Authentication Required')
            ...
            Called Response.send_to_handler(...)
            """ % vars()
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

    def test_checkid_setup_wrong_session_returns_wrong_auth(self):
        """ OpenID checkid_setup with wrong session should request login """
        for params_key in [
            'openid-query-checkid_setup-no-session',
            'openid-query-checkid_setup-other-session',
            ]:
            params = self.valid_requests[params_key]
            args = params['args']
            server = args['server']
            instance = self.handler_class(**args)
            expect_stdout = """\
                Called openid_server.decodeRequest(...)
                Called ResponseHeader_class(200)
                Called Page_class('Authentication Required')
                ...
                Called Response.send_to_handler(...)
                """
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
                )

    def test_checkid_with_session_returns_success(self):
        """ OpenID checkid with right session should succeed """
        for params_key in [
            'openid-query-checkid_immediate-right-session',
            'openid-query-checkid_setup-right-session',
            ]:
            params = self.valid_requests[params_key]
            args = params['args']
            server = args['server']
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


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
