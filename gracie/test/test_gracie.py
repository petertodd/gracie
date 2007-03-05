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


class Test_OpenIDServer(scaffold.TestCase):
    """ Test cases for OpenIDServer class """

    def setUp(self):
        """ Set up test fixtures """

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
            instance = gracie.OpenIDServer(**args)
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_apps
        )

        self.stdout_prev = sys.stdout
        self.test_stdout = StringIO()
        sys.stdout = self.test_stdout

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev

    def test_instantiate(self):
        """ New OpenIDServer instance should be created """

        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_opts_version(self):
        """ OpenIDServer instance should perform version action """

        argv = ["--version"]
        version_prev = gracie.__version__
        version_test = "Foo.Boo"
        gracie.__version__ = version_test
        expect_stdout = """\
            ...%(version)s...
            """ % dict(version=version_test)
        self.failUnlessRaises(SystemExit,
            gracie.OpenIDServer, argv=argv
        )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )
        gracie.__version__ = version_prev

    def test_opts_help(self):
        """ OpenIDServer instance should perform help action """

        argv = ["--help"]
        expect_stdout = """\
            usage: ...
            """
        self.failUnlessRaises(SystemExit,
            gracie.OpenIDServer, argv=argv
        )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_opts_loglevel(self):
        """ OpenIDServer instance should accept log-level setting """
        want_loglevel = "DEBUG"
        argv = ["--log-level", want_loglevel]
        instance = gracie.OpenIDServer(argv=argv)
        self.failUnlessEqual(want_loglevel, instance.opts.loglevel)

    def test_serve_forever_is_callable(self):
        """ OpenIDServer.serve_forever should be callable """
        self.failUnless(callable(gracie.OpenIDServer.serve_forever))


class Test_main(scaffold.TestCase):
    """ Test cases for __main__ function """

    def setUp(self):
        """ Set up test fixtures """
        mock_server_class = Mock('OpenIDServer_class')
        mock_server_class.mock_returns = Mock('OpenIDServer')
        self.mainfunc = gracie.__main__

        self.stdout_prev = sys.stdout
        self.test_stdout = StringIO()
        sys.stdout = self.test_stdout

        self.server_class_prev = gracie.OpenIDServer
        gracie.OpenIDServer = mock_server_class

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        gracie.OpenIDServer = self.server_class_prev

    def test_is_callable(self):
        """ __main__ function should be callable """
        self.failUnless(callable(self.mainfunc))

    def test_instantiates_server_class(self):
        """ __main__() should instantiate the app server class """
        args = dict()
        expect_stdout = """\
            Called OpenIDServer_class(...)
            ..."""
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_defaults_argv_to_sys_argv(self):
        """ __main__() should default commandline arguments to sys.argv """
        args = dict()
        expect_stdout = """\
            Called OpenIDServer_class(%(argv)s)
            ...""" % dict(argv=sys.argv)
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_passes_argv_to_server(self):
        """ __main__() should pass commandline arguments to server """
        argv = ["foo"]
        args = dict(
            argv=argv,
        )
        expect_stdout = """\
            Called OpenIDServer_class(%(argv)s)
            ...""" % dict(argv=argv)
        self.mainfunc(**args)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.test_stdout.getvalue()
        )

    def test_invokes_serve_forever(self):
        """ __main__() should invoke server's serve_forever() method """
        argv = ["foo"]
        args = dict(argv=argv)
        expect_stdout = """\
            Called OpenIDServer_class(%(argv)s)
            Called OpenIDServer.serve_forever(...)
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
