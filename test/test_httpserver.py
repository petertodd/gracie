#! /usr/bin/python
# -*- coding: utf-8 -*-

# test/test_httpserver.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for httpserver module
"""

import sys
from StringIO import StringIO

import scaffold
from scaffold import Mock
from test_server import stub_server_bind, make_default_opts
from test_gracied import Stub_GracieServer

from gracie import httpserver


class Test_net_location(scaffold.TestCase):
    """ Test cases for net_location function """

    def setUp(self):
        """ Set up test fixtures """
        self.default_port_prev = httpserver.default_port
        self.default_port_test = 9779
        httpserver.default_port = self.default_port_test

    def tearDown(self):
        """ Tear down test fixtures """
        httpserver.default_port = self.default_port_prev

    def test_combines_components_to_location(self):
        """ net_location() should combine components to net location """
        http_port = 80
        locations = {
            ("foo", None): "foo",
            ("foo", http_port): "foo",
            ("foo", self.default_port_test):
                "foo:%s" % self.default_port_test,
            ("foo", 2468): "foo:2468",
            }

        for (host, port), expect_location in locations.items():
            location = httpserver.net_location(host, port)
            self.failUnlessEqual(expect_location, location)


class Stub_HTTPRequestHandler(object):
    """ Stub class for HTTPRequestHandler """


class Test_HTTPServer(scaffold.TestCase):
    """ Test cases for HTTPServer class """

    def setUp(self):
        """ Set up test fixtures """

        self.mock_outfile = StringIO()

        self.server_class = httpserver.HTTPServer

        self.stub_handler_class = Stub_HTTPRequestHandler
        self.mock_handler_class = Mock('HTTPRequestHandler')

        self.server_bind_prev = httpserver.BaseHTTPServer.server_bind
        httpserver.BaseHTTPServer.server_bind = stub_server_bind

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
            opts = make_default_opts()
            gracie_server = params.setdefault(
                'gracie_server', Stub_GracieServer(address, opts)
                )
            if not args:
                args = dict(
                    server_address = params['address'],
                    RequestHandlerClass = params['handler_class'],
                    gracie_server = params['gracie_server'],
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
        httpserver.BaseHTTPServer.server_bind = self.server_bind_prev
        scaffold.mock_restore()

    def test_instantiate(self):
        """ New HTTPServer instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failIfIs(None, instance)

    def test_version_as_specified(self):
        """ HTTPServer should have specified version string """
        params = self.valid_servers['simple']
        server_module = sys.modules['gracie.server']
        scaffold.mock(
            "server_module.version", outfile=self.mock_outfile)
        version_test = Stub_GracieServer.version
        server_module.version.version_full = version_test
        instance = self.server_class(**params['args'])
        self.failUnlessEqual(version_test, instance.version)

    def test_request_handler_class_as_specified(self):
        """ HTTPServer should have specified RequestHandlerClass """
        for key, params in self.iterate_params():
            instance = params['instance']
            handler_class = params['handler_class']
            self.failUnlessEqual(
                handler_class, instance.RequestHandlerClass
                )

    def test_gracie_server_as_specified(self):
        """ HTTPServer should have specified Gracie server instance """
        for key, params in self.iterate_params():
            instance = params['instance']
            gracie_server = params['gracie_server']
            self.failUnlessEqual(
                gracie_server, instance.gracie_server
                )

    def test_serve_forever_is_callable(self):
        """ HTTPServer.serve_forever should be callable """
        self.failUnless(callable(self.server_class.serve_forever))


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
