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

import httprequest


class Stub_Logger(object):
    """ Stub class for Logger """

    def log(self, format, *args, **kwargs):
        """ Log a message """

    error = log
    warn = log
    info = log

class Stub_SessionManager(object):
    """ Stub class for SessionManager """

    def __init__(self):
        """ Set up a new instance """
        self._sessions = dict()
        self.create_session("fred")

    def create_session(self, username):
        session_id = "DEADBEEF-%(username)s" % locals()
        self._sessions[session_id] = username
        return session_id

    def get_session(self, session_id):
        return self._sessions[session_id]

    def remove_session(self, session_id):
        del self._sessions[session_id]

class Stub_OpenIDError(Exception):
    """ Stub error class for openid module """

class Stub_OpenIDServer(object):
    """ Stub class for an OpenID protocol server """

class Stub_OpenIDResponse(object):
    """ Stub class for an OpenID protocol response """

    def __init__(self):
        self.code = 200
        self.headers = [("openid", "yes")]
        self.body = "OpenID response"

class Stub_HTTPServer(object):
    """ Stub class for HTTPServer """

    def __init__(self):
        """ Set up a new instance """
        self.logger = Stub_Logger()
        self.openid_server = Stub_OpenIDServer()
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
        self.cookie_name_prefix_prev = httprequest.cookie_name_prefix
        httprequest.Response = Mock('Response_class')
        httprequest.Response.mock_returns = Mock('Response')
        httprequest.ResponseHeader = Mock('ResponseHeader_class')
        httprequest.ResponseHeader.mock_returns = Mock('ResponseHeader')
        httprequest.pagetemplate.Page = Mock('Page_class')
        httprequest.pagetemplate.Page.mock_returns = Mock('Page')
        httprequest.cookie_name_prefix = "TEST_"
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
            'openid-query-checkid': dict(
                request = Stub_Request("GET", "/openidserver",
                    query = {
                        "openid.mode": "checkid_immediate",
                        "openid.identity": "http://example.com/fred",
                        "openid.return_to": "http://example.org/",
                    },
                ),
            ),
        }

        logging.basicConfig(stream=self.stdout_test)

        for key, params in self.valid_requests.items():
            args = params.get('args')
            request = params['request']
            address = params.setdefault('address', ("", 0))
            http_server = params.setdefault('server',
                                            Stub_HTTPServer())
            http_server.openid_server = mock_openid_server
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

        version = httprequest.__version__
        self.expect_server_version = "Gracie/%(version)s" % locals()
        python_version = sys.version.split()[0]
        self.expect_sys_version = "Python/%(python_version)s" % locals()

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        httprequest.Response = self.response_class_prev
        httprequest.ResponseHeader = self.response_header_class_prev
        httprequest.pagetemplate.Page = self.page_class_prev
        httprequest.cookie_name_prefix = self.cookie_name_prefix_prev

    def test_instantiate(self):
        """ New HTTPRequestHandler instance should be created """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            self.failUnless(instance is not None)

    def test_server_as_specified(self):
        """ HTTPRequestHandler should have specified server attribute """
        for key, params in self.iterate_params():
            instance = self.handler_class(**params['args'])
            http_server = params['server']
            self.failUnlessEqual(http_server, instance.server)

    def test_server_version_as_specified(self):
        """ HTTPRequestHandler should report module version """
        server_version = self.handler_class.server_version
        self.failUnlessEqual(self.expect_server_version, server_version)

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

    def test_internal_error_sends_server_error_response(self):
        """ When an error condition is raised, should send Server Error """
        def raise_Error(_):
            raise StandardError("Testing error")
        dispatch_method_prev = self.handler_class._dispatch
        self.handler_class._dispatch = raise_Error

        params = self.valid_requests['get-root']
        instance = self.handler_class(**params['args'])
        expect_stdout = """\
            Called ResponseHeader_class(500)
            ...
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )
        self.handler_class._dispatch = dispatch_method_prev

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
        http_server = args['server']
        http_server.openid_server.decodeRequest = raise_ProtocolError
        instance = self.handler_class(**args)
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
        http_server = args['server']
        openid_server = http_server.openid_server
        openid_server.decodeRequest.mock_returns = object()
        openid_server.encodeResponse.mock_returns = Stub_OpenIDResponse()
        instance = self.handler_class(**args)
        expect_stdout = """\
            Called openid_server.decodeRequest(...)
            Called openid_server.handleRequest(...)
            Called openid_server.encodeResponse(...)
            Called ResponseHeader_class(200)
            Called ResponseHeader.fields.extend([('openid', 'yes')])
            Called Response_class(..., 'OpenID response')
            Called Response.send_to_handler(...)
            """
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
