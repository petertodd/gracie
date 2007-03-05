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

import scaffold
from scaffold import Mock

import server


class Stub_Logger(object):
    """ Stub class for Logger """

    def log(self, format, *args, **kwargs):
        """ Log a message """

class Stub_OpenIDServer(object):
    """ Stub class for OpenIDServer """

    def __init__(self):
        """ Set up a new instance """
        self.logger = Stub_Logger()

class Stub_TCPConnection(object):
    """ Stub class for TCP connection """

    def __init__(self, text):
        """ Set up a new instance """
        self._text = text

    def makefile(self, mode, bufsize):
        """ Make a file handle to the connection stream """
        return StringIO(self._text)

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
            'get_foo': dict(
                request_text = "GET /foo HTTP/1.1",
                command = "GET",
                path = "/foo",
                version = "HTTP/1.1",
            ),
        }

        for key, params in self.valid_requests.items():
            args = params.get('args')
            request_text = params.get('request_text', "")
            request = Stub_TCPConnection(request_text)
            params['request'] = request
            address = params.setdefault('address', ("", 0))
            http_server = params.setdefault('server',
                                            Stub_OpenIDServer())
            if not args:
                args = dict(
                    request = request,
                    client_address = address,
                    server = http_server,
                )
            instance = self.handler_class(**args)
            params['instance'] = instance

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

    def test_instantiate(self):
        """ New OpenIDRequestHandler instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_server_version_as_specified(self):
        """ OpenIDRequestHandler should report module version """
        server_version = self.handler_class.server_version
        self.failUnlessEqual(self.expect_server_version, server_version)

    def test_version_string_as_specified(self):
        """ OpenIDRequestHandler should report expected version string """
        expect_sys_version = self.expect_sys_version
        expect_server_version = self.expect_server_version
        expect_version_string = (
            "%(expect_server_version)s %(expect_sys_version)s"
            % locals() )
        instance = self.valid_requests['simple']['instance']
        version_string = instance.version_string()
        self.failUnlessEqual(expect_version_string, version_string)

    def test_log_message_to_logger(self):
        """ Request should log messages using server's logger """
        params = self.valid_requests['simple']
        instance = params['instance']
        http_server = params['server']
        http_server.logger = Mock("logger")
        http_server.logger.log = Mock("logger.log")
        msg_format = "Foo"
        msg_args = ("spam", "eggs")
        expect_stdout = """\
            Called logger.log(%(msg_format)r, ...)
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
            instance = params['instance']
            command = params['command']
            self.failUnlessEqual(command, instance.command)

    def test_path_from_request(self):
        """ Request path attribute should come from request text """
        for key, params in self.iterate_params():
            request_text = params.get('request_text')
            if not request_text:
                continue
            instance = params['instance']
            path = params['path']
            self.failUnlessEqual(path, instance.path)

    def test_request_version_from_request(self):
        """ Request HTTP version attribute should come from request text """
        for key, params in self.iterate_params():
            request_text = params.get('request_text')
            if not request_text:
                continue
            instance = params['instance']
            request_version = params['version']
            self.failUnlessEqual(request_version, instance.request_version)


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
        import logging
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
