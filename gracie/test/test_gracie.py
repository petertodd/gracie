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

module_name = 'gracie'
module_file_under_test = os.path.join(scaffold.code_dir, module_name)
gracie = scaffold.make_module_from_file(
    module_name, module_file_under_test
)


class Stub_OpenIDServer(object):
    """ Stub class for OpenIDServer """
    def __init__(self, server_address, RequestHandlerClass):
        """ Set up a new instance """

class Stub_OpenIDRequestHandler(object):
    """ Stub class for OpenIDRequestHandler """

class Test_Gracie(scaffold.TestCase):
    """ Test cases for Gracie class """
    def setUp(self):
        """ Set up test fixtures """

        self.app_class = gracie.Gracie

        self.stdout_prev = sys.stdout
        self.test_stdout = StringIO()
        sys.stdout = self.test_stdout

        self.stub_server_class = Stub_OpenIDServer
        self.mock_server_class = Mock('OpenIDServer_class')
        self.mock_server_class.mock_returns = Mock('OpenIDServer')

        self.server_class_prev = gracie.OpenIDServer
        gracie.OpenIDServer = self.stub_server_class
        self.handler_class_prev = gracie.OpenIDRequestHandler
        gracie.RequestHandlerClass = Stub_OpenIDRequestHandler
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
        gracie.OpenIDServer = self.server_class_prev
        gracie.OpenIDRequestHandler = self.handler_class_prev
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
            expect_stdout, self.test_stdout.getvalue()
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
            expect_stdout, self.test_stdout.getvalue()
        )
        gracie.__version__ = version_prev

    def test_opts_help(self):
        """ Gracie instance should perform help action """

        argv = ["--help"]
        expect_stdout = """\
            usage: ...
            """
        gracie.OpenIDServer = self.mock_server_class
        self.failUnlessRaises(SystemExit,
            self.app_class, argv=argv
        )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_opts_loglevel(self):
        """ Gracie instance should accept log-level setting """

        want_loglevel = "DEBUG"
        argv = ["--log-level", want_loglevel]
        gracie.OpenIDServer = self.mock_server_class
        instance = self.app_class(argv=argv)
        self.failUnlessEqual(want_loglevel, instance.opts.loglevel)

    def test_instantiates_server(self):
        """ Gracie instance should create a new server instance """
        args = self.valid_apps['simple']['args']
        host = gracie.default_host
        port = gracie.default_port
        expect_stdout = """\
            Called OpenIDServer_class(
                (%(host)r, %(port)r),
                <class 'httprequest.OpenIDRequestHandler'>)
            ...""" % locals()
        gracie.OpenIDServer = self.mock_server_class
        instance = self.app_class(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )
        self.failUnless(instance.server is not None)

    def test_run_is_callable(self):
        """ Gracie.run should be callable """
        self.failUnless(callable(self.app_class.run))

    def test_run_starts_server(self):
        """ Gracie.run should start OpenIDServer """
        args = self.valid_apps['simple']['args']
        port = gracie.default_port
        expect_stdout = """\
            ...
            Called OpenIDServer.serve_forever()
            """
        gracie.OpenIDServer = self.mock_server_class
        instance = self.app_class(**args)
        instance.run()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )


class Test_main(scaffold.TestCase):
    """ Test cases for __main__ function """

    def setUp(self):
        """ Set up test fixtures """
        mock_app_class = Mock('Gracie_class')
        mock_app_class.mock_returns = Mock('Gracie')
        self.mainfunc = gracie.__main__

        self.stdout_prev = sys.stdout
        self.test_stdout = StringIO()
        sys.stdout = self.test_stdout

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
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_defaults_argv_to_sys_argv(self):
        """ __main__() should default commandline arguments to sys.argv """
        args = dict()
        expect_stdout = """\
            Called Gracie_class(%(argv)s)
            ...""" % dict(argv=sys.argv)
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
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
            expect_stdout, self.test_stdout.getvalue()
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
            expect_stdout, self.test_stdout.getvalue()
        )


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
