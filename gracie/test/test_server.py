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


class Stub_Logger(object):
    """ Stub class for Logger """

    def log(self, format, *args, **kwargs):
        """ Log a message """

class Stub_Page(object):
    """ Stub class for Page """
    def __init__(self, title):
        """ Set up a new instance """
    def serialise(self):
        """ Serialise the page content """

class Stub_OpenIDServer(object):
    """ Stub class for OpenIDServer """

    def __init__(self):
        """ Set up a new instance """
        self.logger = Stub_Logger()
        self.PageClass = Stub_Page

class Stub_EmptyFile(object):
    """ Stub class for a null file

    Always empty when read
    """
    def __init__(self): self.closed = False
    def flush(self): pass
    def close(self): self.closed = True
    def next(self): raise StopIteration
    def read(self, size=None): return ""
    def readline(self, size=None): return ""

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

class Mock_TCPConnection(object):
    """ Allow writing to a mock connection """
    def __init__(self, text):
        self._text = text
    def makefile(self, mode, bufsize):
        """ Make a file handle to the connection stream """
        conn_file = None
        if mode.startswith('r'):
            conn_file = StringIO(self._text)
            conn_file.seek(0)
        elif mode.startswith('w'):
            conn_file = Mock('TCPConnection.wfile')
        return conn_file

class Test_OpenIDRequestHandler(scaffold.TestCase):
    """ Test cases for OpenIDRequestHandler class """

    def setUp(self):
        """ Set up test fixtures """
        self.handler_class = server.OpenIDRequestHandler

        self.stdout_prev = sys.stdout
        self.test_stdout = StringIO()
        sys.stdout = self.test_stdout

        self.valid_requests = {
            'simple': dict(
            ),
            'get-foo': dict(
                request_text = "GET /foo HTTP/1.1",
                command = "GET",
                path = "/foo",
                version = "HTTP/1.1",
            ),
            'id-fred': dict(
                request_text = "GET /id/fred HTTP/1.1",
                command = "GET",
                path = "/id/fred",
                version = "HTTP/1.1",
            ),
        }

        logging.basicConfig(stream=self.test_stdout)
        test_logger = logging.getLogger(server.logger_name)

        for key, params in self.valid_requests.items():
            args = params.get('args')
            request_text = params.get('request_text', "")
            request = Stub_TCPConnection(request_text)
            params['request'] = request
            address = params.setdefault('address', ("", 0))
            http_server = params.setdefault('server',
                                            Stub_OpenIDServer())
            http_server.logger = test_logger
            http_server.PageClass = Stub_Page
            if not args:
                args = dict(
                    request = request,
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

    def make_instance_from_args(self, args, handler_class=None):
        """ Construct an instance from the specified arguments """
        if handler_class is None:
            handler_class = self.handler_class
        return handler_class(**args)

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev

    def test_instantiate(self):
        """ New OpenIDRequestHandler instance should be created """
        for key, params in self.iterate_params():
            instance = self.make_instance_from_args(params['args'])
            self.failUnless(instance is not None)

    def test_server_as_specified(self):
        """ OpenIDRequestHandler should have specified server attribute """
        for key, params in self.iterate_params():
            instance = self.make_instance_from_args(params['args'])
            http_server = params['server']
            self.failUnlessEqual(http_server, instance.server)

    def test_server_version_as_specified(self):
        """ OpenIDRequestHandler should report module version """
        server_version = self.handler_class.server_version
        self.failUnlessEqual(self.expect_server_version, server_version)

    def test_version_string_as_specified(self):
        """ OpenIDRequestHandler should report expected version string """
        params = self.valid_requests['simple']
        instance = self.make_instance_from_args(params['args'])
        expect_sys_version = self.expect_sys_version
        expect_server_version = self.expect_server_version
        expect_version_string = (
            "%(expect_server_version)s %(expect_sys_version)s"
            % locals() )
        version_string = instance.version_string()
        self.failUnlessEqual(expect_version_string, version_string)

    def test_log_message_to_logger(self):
        """ Request should log messages using server's logger """
        params = self.valid_requests['simple']
        instance = self.make_instance_from_args(params['args'])
        http_server = params['server']
        http_server.logger = Mock("logger")
        http_server.logger.log = Mock("logger.log")
        msg_format = "Foo"
        msg_level = logging.INFO
        msg_args = ("spam", "eggs")
        expect_stdout = """\
            Called logger.log(%(msg_level)r, %(msg_format)r, ...)
            """ % locals()
        instance.log_message(msg_format, *msg_args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_command_from_request(self):
        """ Request command attribute should come from request text """
        for key, params in self.iterate_params():
            request_text = params.get('request_text')
            if not request_text:
                continue
            command = params['command']
            instance = self.make_instance_from_args(params['args'])
            self.failUnlessEqual(command, instance.command)

    def test_path_from_request(self):
        """ Request path attribute should come from request text """
        for key, params in self.iterate_params():
            request_text = params.get('request_text')
            if not request_text:
                continue
            path = params['path']
            instance = self.make_instance_from_args(params['args'])
            self.failUnlessEqual(path, instance.path)

    def test_request_version_from_request(self):
        """ Request HTTP version attribute should come from request text """
        for key, params in self.iterate_params():
            request_text = params.get('request_text')
            if not request_text:
                continue
            request_version = params['version']
            instance = self.make_instance_from_args(params['args'])
            self.failUnlessEqual(request_version, instance.request_version)

    def _make_http_server_with_mocked_page_class(self):
        Page = Mock('Page')
        Page.serialise.mock_returns = "mock_page_content"
        http_server = Mock('OpenIDServer')
        http_server.PageClass = Mock('PageClass')
        http_server.PageClass.mock_returns = Page
        return http_server

    def test_bogus_request_returns_not_found(self):
        """ Request for a bogus URL should return Not Found response """
        params = self.valid_requests['get-foo']
        args = params['args']
        request = Mock_TCPConnection(params['request_text'])
        args['request'] = request
        http_server = self._make_http_server_with_mocked_page_class()
        args['server'] = http_server
        instance = self.make_instance_from_args(args)
        expect_stdout = """\
            Called PageClass(title='Not found')
            ...
            Called TCPConnection.wfile.write('HTTP/1.0 404 Not found\\r\\n')
            ...
            """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_request_get_id_returns_user_page(self):
        """ Request for user ID should return identity page """                
        params = self.valid_requests['id-fred']
        args = params['args']
        request = Mock_TCPConnection(params['request_text'])
        args['request'] = request
        http_server = self._make_http_server_with_mocked_page_class()
        args['server'] = http_server
        instance = self.make_instance_from_args(args)
        identity = "fred"
        expect_stdout = """\
           Called PageClass(title='...%(identity)s...')
           ...
           Called TCPConnection.wfile.write('HTTP/1.0 200 OK\\r\\n')
           ...
           Called TCPConnection.wfile.write('\\r\\n')
           Called TCPConnection.wfile.write('mock_page_content')
           Called TCPConnection.wfile.close()
           """ % locals()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
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
        self.test_stdout = StringIO()
        sys.stdout = self.test_stdout

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
        logger_name_prev = server.logger_name
        logger_name_test = "Foo.Bar"
        server.logger_name = logger_name_test
        expect_logger = logging.getLogger(logger_name_test)
        args = self.valid_servers['simple']['args']
        instance = self.server_class(**args)
        self.failUnlessEqual(expect_logger, instance.logger)
        server.logger_name = logger_name_prev

    def test_request_handler_class_as_specified(self):
        """ OpenIDServer should have specified RequestHandlerClass """
        for key, params in self.iterate_params():
            instance = params['instance']
            handler_class = params['handler_class']
            self.failUnlessEqual(handler_class,
                                 instance.RequestHandlerClass)

    def test_serve_forever_is_callable(self):
        """ OpenIDServer.serve_forever should be callable """
        self.failUnless(callable(self.server_class.serve_forever))


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
