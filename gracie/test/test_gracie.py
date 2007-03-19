#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test_gracie.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for gracie application module
"""

import sys
import os
from StringIO import StringIO

import scaffold
from scaffold import Mock
from test_httprequest import Stub_GracieServer

module_name = 'gracie'
module_file_under_test = os.path.join(scaffold.code_dir, module_name)
gracie = scaffold.make_module_from_file(
    module_name, module_file_under_test
)


class Stub_GracieServer(object):
    """ Stub class for GracieServer """

    version = "3.14.test"

    def __init__(self, socket_params, opts):
        """ Set up a new instance """


class Test_Gracie(scaffold.TestCase):
    """ Test cases for Gracie class """
    def setUp(self):
        """ Set up test fixtures """

        self.app_class = gracie.Gracie

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.stub_server_class = Stub_GracieServer
        self.mock_server_class = Mock('GracieServer_class')
        self.mock_server_class.mock_returns = Mock('GracieServer')

        self.server_class_prev = gracie.GracieServer
        gracie.GracieServer = self.stub_server_class
        self.default_port_prev = gracie.default_port
        gracie.default_port = 7654

        self.valid_apps = {
            'simple': dict(
                args = dict(),
            ),
            'argv_loglevel_debug': dict(
                args = dict(),
                options = ["--log-level", "debug"],
            ),
            'change-host': dict(
                args = dict(),
                options = ["--host", "frobnitz"],
                host = "frobnitz",
            ),
            'change-port': dict(
                args = dict(),
                options = ["--port", "9779"],
                port = 9779,
            ),
            'change-address': dict(
                args = dict(),
                options = ["--host", "frobnitz", "--port", "9779"],
                host = "frobnitz",
                port = 9779,
            ),
        }

        for key, params in self.valid_apps.items():
            args = params['args']
            argv = []
            options = params.get('options', None)
            if options:
                argv.extend(options)
            args['argv'] = argv
            instance = self.app_class(**args)
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_apps
        )

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        gracie.GracieServer = self.server_class_prev
        gracie.default_port = self.default_port_prev

    def test_instantiate(self):
        """ New Gracie instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_configures_logging(self):
        """ New Gracie instance should configure logging """
        params = self.valid_apps['simple']
        args = params['args']
        logging_prev = gracie.logging
        gracie.logging = Mock('logging')
        expect_stdout = """\
           Called logging.basicConfig(...)
           """
        instance = self.app_class(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )
        gracie.logging = logging_prev

    def test_opts_version(self):
        """ Gracie instance should perform version action """

        argv = ["--version"]
        version_prev = gracie.__version__
        version_test = "Foo.Boo"
        gracie.__version__ = version_test
        expect_stdout = """\
            ...%(version)s...
            """ % dict(version=version_test)
        self.failUnlessRaises(SystemExit,
            self.app_class, argv=argv
        )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )
        gracie.__version__ = version_prev

    def test_opts_help(self):
        """ Gracie instance should perform help action """
        argv = ["--help"]
        expect_stdout = """\
            usage: ...
            """
        gracie.GracieServer = self.mock_server_class
        self.failUnlessRaises(SystemExit,
            self.app_class, argv=argv
        )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_opts_loglevel(self):
        """ Gracie instance should accept log-level setting """
        want_loglevel = "DEBUG"
        argv = ["--log-level", want_loglevel]
        instance = self.app_class(argv=argv)
        self.failUnlessEqual(want_loglevel, instance.opts.loglevel)

    def test_opts_datadir(self):
        """ Gracie instance should accept data-dir setting """
        want_dir = "/foo/bar"
        argv = ["--data-dir", want_dir]
        instance = self.app_class(argv=argv)
        self.failUnlessEqual(want_dir, instance.opts.datadir)

    def test_opts_host(self):
        """ Gracie instance should accept host setting """
        want_host = "frobnitz"
        argv = ["--host", want_host]
        instance = self.app_class(argv=argv)
        self.failUnlessEqual(want_host, instance.opts.host)

    def test_opts_port(self):
        """ Gracie instance should accept port setting """
        want_port = 9779
        argv = ["--port", want_port]
        instance = self.app_class(argv=argv)
        self.failUnlessEqual(want_port, instance.opts.port)

    def test_instantiates_server(self):
        """ Gracie instance should create a new server instance """
        params = self.valid_apps['simple']
        args = params['args']
        host = gracie.default_host
        port = gracie.default_port
        expect_stdout = """\
            Called GracieServer_class(
                (%(host)r, %(port)r),
                <Values ...>)
            ...""" % locals()
        gracie.GracieServer = self.mock_server_class
        instance = self.app_class(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )
        self.failUnless(instance.server is not None)

    def test_sets_specified_socket_params(self):
        """ Should set the server on the specified host:port """
        for key, params in self.iterate_params():
            args = params['args']
            default_address = (
                gracie.default_host, gracie.default_port
            )
            host = params.get('host', gracie.default_host)
            port = params.get('port', gracie.default_port)
            if (host, port) == default_address:
                continue
            expect_stdout = """\
                Called GracieServer_class(
                    (%(host)r, %(port)r),
                    <Values ...>)
                ...""" % locals()
            gracie.GracieServer = self.mock_server_class
            instance = self.app_class(**args)
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
            )
            self.stdout_test.truncate(0)

    def test_run_is_callable(self):
        """ Gracie.run should be callable """
        self.failUnless(callable(self.app_class.run))

    def test_run_starts_server(self):
        """ Gracie.run should start GracieServer """
        args = self.valid_apps['simple']['args']
        port = gracie.default_port
        expect_stdout = """\
            ...
            Called GracieServer.serve_forever()
            """
        gracie.GracieServer = self.mock_server_class
        instance = self.app_class(**args)
        instance.run()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )


class Test_main(scaffold.TestCase):
    """ Test cases for __main__ function """

    def setUp(self):
        """ Set up test fixtures """
        mock_app_class = Mock('Gracie_class')
        mock_app_class.mock_returns = Mock('Gracie')
        self.mainfunc = gracie.__main__

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.app_class_prev = gracie.Gracie
        gracie.Gracie = mock_app_class

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        gracie.Gracie = self.app_class_prev

    def test_is_callable(self):
        """ __main__ function should be callable """
        self.failUnless(callable(self.mainfunc))

    def test_instantiates_app_class(self):
        """ __main__() should instantiate the application class """
        args = dict()
        expect_stdout = """\
            Called Gracie_class(...)
            ..."""
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_defaults_argv_to_sys_argv(self):
        """ __main__() should default commandline arguments to sys.argv """
        args = dict()
        expect_stdout = """\
            Called Gracie_class(%(argv)s)
            ...""" % dict(argv=sys.argv)
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_passes_argv_to_server(self):
        """ __main__() should pass commandline arguments to application """
        argv = ["foo"]
        args = dict(
            argv=argv,
        )
        expect_stdout = """\
            Called Gracie_class(%(argv)s)
            ...""" % dict(argv=argv)
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_invokes_run(self):
        """ __main__() should invoke app's run() method """
        argv = ["foo"]
        args = dict(argv=argv)
        expect_stdout = """\
            Called Gracie_class(%(argv)s)
            Called Gracie.run(...)
        """ % dict(argv=argv)
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
