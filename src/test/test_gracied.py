#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test_gracied.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for gracied daemon module
"""

import sys
import os
from StringIO import StringIO

import scaffold
from scaffold import Mock
from test_httprequest import Stub_GracieServer

module_name = 'gracied'
module_file_under_test = os.path.join(scaffold.parent_dir, module_name)
gracied = scaffold.make_module_from_file(
    module_name, module_file_under_test
)


class Stub_GracieServer(object):
    """ Stub class for GracieServer """

    version = "3.14.test"

    def __init__(self, socket_params, opts):
        """ Set up a new instance """

    def serve_forever(self):
        pass


class Test_Gracie(scaffold.TestCase):
    """ Test cases for Gracie class """
    def setUp(self):
        """ Set up test fixtures """

        self.app_class = gracied.Gracie

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.stub_server_class = Stub_GracieServer
        self.mock_server_class = Mock('GracieServer_class')
        self.mock_server_class.mock_returns = Mock('GracieServer')

        self.server_class_prev = gracied.GracieServer
        gracied.GracieServer = self.stub_server_class
        self.default_port_prev = gracied.default_port
        gracied.default_port = 7654

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
            'change-root-url': dict(
                args = dict(),
                options = ["--root-url", "http://spudnik/spam"],
                root_url = "http://spudnik/spam",
            ),
            'change-address-and-root-url': dict(
                args = dict(),
                options = [
                    "--host", "frobnitz", "--port", "9779",
                    "--root-url", "http://spudnik/spam",
                ],
                host = "frobnitz",
                port = 9779,
                root_url = "http://frobnitz/spam",
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
        gracied.GracieServer = self.server_class_prev
        gracied.default_port = self.default_port_prev

    def test_instantiate(self):
        """ New Gracie instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_configures_logging(self):
        """ New Gracie instance should configure logging """
        params = self.valid_apps['simple']
        args = params['args']
        logging_prev = gracied.logging
        gracied.logging = Mock('logging')
        expect_stdout = """\
           Called logging.basicConfig(...)
           """
        instance = self.app_class(**args)
        gracied.logging = logging_prev
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_opts_version(self):
        """ Gracie instance should perform version action """

        argv = ["--version"]
        version_prev = gracied.__version__
        version_test = "Foo.Boo"
        gracied.__version__ = version_test
        expect_stdout = """\
            ...%(version)s...
            """ % dict(version=version_test)
        self.failUnlessRaises(SystemExit,
            self.app_class, argv=argv
        )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )
        gracied.__version__ = version_prev

    def test_opts_help(self):
        """ Gracie instance should perform help action """
        argv = ["--help"]
        expect_stdout = """\
            usage: ...
            """
        gracied.GracieServer = self.mock_server_class
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

    def test_opts_root_url(self):
        """ Gracie instance should accept root_url setting """
        want_url = "http://spudnik/spam"
        argv = ["--root-url", want_url]
        instance = self.app_class(argv=argv)
        self.failUnlessEqual(want_url, instance.opts.root_url)

    def test_instantiates_server(self):
        """ Gracie instance should create a new server instance """
        params = self.valid_apps['simple']
        args = params['args']
        host = gracied.default_host
        port = gracied.default_port
        expect_stdout = """\
            Called GracieServer_class(
                (%(host)r, %(port)r),
                <Values ...>)
            ...""" % locals()
        gracied.GracieServer = self.mock_server_class
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
                gracied.default_host, gracied.default_port
            )
            host = params.get('host', gracied.default_host)
            port = params.get('port', gracied.default_port)
            if (host, port) == default_address:
                continue
            expect_stdout = """\
                Called GracieServer_class(
                    (%(host)r, %(port)r),
                    <Values ...>)
                ...""" % locals()
            gracied.GracieServer = self.mock_server_class
            instance = self.app_class(**args)
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
            )
            self.stdout_test.truncate(0)

    def test_run_is_callable(self):
        """ Gracie.run should be callable """
        self.failUnless(callable(self.app_class.run))

    def test_run_calls_become_daemon(self):
        """ Gracie.run should attempt to become a daemon """
        params = self.valid_apps['simple']
        gracied.become_daemon = Mock('become_daemon')
        expect_stdout = """\
            Called become_daemon()
            """
        instance = params['instance']
        instance.run()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
        )

    def test_run_starts_server(self):
        """ Gracie.run should start GracieServer if child fork """
        args = self.valid_apps['simple']['args']
        port = gracied.default_port
        expect_stdout = """\
            ...
            Called GracieServer.serve_forever()
            """
        gracied.GracieServer = self.mock_server_class
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
        self.mainfunc = gracied.__main__

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.app_class_prev = gracied.Gracie
        gracied.Gracie = mock_app_class

    def tearDown(self):
        """ Tear down test fixtures """
        sys.stdout = self.stdout_prev
        gracied.Gracie = self.app_class_prev

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
