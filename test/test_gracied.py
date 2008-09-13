#! /usr/bin/python
# -*- coding: utf-8 -*-

# test/test_gracied.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
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

module_name = 'gracied'
module_file_under_test = os.path.join(scaffold.bin_dir, module_name)
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

        self.mock_outfile = StringIO()

        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test

        self.parser_error_prev = gracied.OptionParser.error
        gracied.OptionParser.error = Mock(
            "OptionParser.error",
            raises=SystemExit)

        self.stub_server_class = Stub_GracieServer
        self.mock_server_class = Mock('GracieServer_class')
        self.mock_server_class.mock_returns = Mock('GracieServer')

        self.server_class_prev = gracied.GracieServer
        gracied.GracieServer = self.stub_server_class
        self.default_port_prev = gracied.default_port
        gracied.default_port = 7654

        self.valid_apps = {
            'simple': dict(
                ),
            'argv_loglevel_debug': dict(
                options = ["--log-level", "debug"],
                ),
            'change-host': dict(
                options = ["--host", "frobnitz"],
                host = "frobnitz",
                ),
            'change-port': dict(
                options = ["--port", "9779"],
                port = 9779,
                ),
            'change-address': dict(
                options = ["--host", "frobnitz", "--port", "9779"],
                host = "frobnitz",
                port = 9779,
                ),
            'change-root-url': dict(
                options = ["--root-url", "http://spudnik/spam"],
                root_url = "http://spudnik/spam",
                ),
            'change-address-and-root-url': dict(
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
            argv = ["progname"]
            options = params.get('options', None)
            if options:
                argv.extend(options)
            params['argv'] = argv
            args = dict(
                argv=argv
                )
            params['args'] = args
            instance = self.app_class(**args)
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_apps
            )

    def tearDown(self):
        """ Tear down test fixtures """
        self.stdout_test.truncate(0)
        sys.stdout = self.stdout_prev
        gracied.OptionParser.error = self.parser_error_prev
        gracied.GracieServer = self.server_class_prev
        gracied.default_port = self.default_port_prev
        scaffold.mock_restore()

    def test_instantiate(self):
        """ New Gracie instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failIfIs(instance, None)

    def test_init_configures_logging(self):
        """ Gracie instance should configure logging """
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

    def test_wrong_arguments_invokes_parser_error(self):
        """ Wrong number of cmdline arguments should invoke parser error """
        gracied.OptionParser.error = Mock(
            "OptionParser.error",
            )
        invalid_argv_params = [
            ["progname", "foo",]
            ]
        expect_stdout = """\
            Called OptionParser.error("...")
            """
        for argv in invalid_argv_params:
            args = dict(argv=argv)
            instance = self.app_class(**args)
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
                )

    def test_opts_version_performs_version_action(self):
        """ Gracie instance should perform version action """
        argv = ["progname", "--version"]
        args = dict(argv=argv)
        scaffold.mock(
            "gracied.version", outfile=self.mock_outfile)
        version_test = "Foo.Boo"
        gracied.version.version_full = version_test
        expect_stdout = """\
            ...%(version_test)s...
            """ % vars()
        self.failUnlessRaises(
            SystemExit,
            self.app_class, **args
            )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_opts_help_performs_help_action(self):
        """ Gracie instance should perform help action """
        argv = ["progname", "--help"]
        args = dict(argv=argv)
        expect_stdout = """\
            Usage: ...
            """
        gracied.GracieServer = self.mock_server_class
        self.failUnlessRaises(
            SystemExit,
            self.app_class, **args
            )
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_opts_loglevel_accepts_specified_value(self):
        """ Gracie instance should accept log-level setting """
        want_loglevel = "DEBUG"
        argv = ["progname", "--log-level", want_loglevel]
        args = dict(argv=argv)
        instance = self.app_class(**args)
        self.failUnlessEqual(want_loglevel, instance.opts.loglevel)

    def test_opts_datadir_accepts_specified_value(self):
        """ Gracie instance should accept data-dir setting """
        want_dir = "/foo/bar"
        argv = ["progname", "--data-dir", want_dir]
        args = dict(argv=argv)
        instance = self.app_class(**args)
        self.failUnlessEqual(want_dir, instance.opts.datadir)

    def test_opts_host_accepts_specified_value(self):
        """ Gracie instance should accept host setting """
        want_host = "frobnitz"
        argv = ["progname", "--host", want_host]
        args = dict(argv=argv)
        instance = self.app_class(**args)
        self.failUnlessEqual(want_host, instance.opts.host)

    def test_opts_port_accepts_specified_value(self):
        """ Gracie instance should accept port setting """
        want_port = 9779
        argv = ["progname", "--port", str(want_port)]
        args = dict(argv=argv)
        instance = self.app_class(**args)
        self.failUnlessEqual(want_port, instance.opts.port)

    def test_opts_root_url_accepts_specified_value(self):
        """ Gracie instance should accept root_url setting """
        want_url = "http://spudnik/spam"
        argv = ["progname", "--root-url", want_url]
        args = dict(argv=argv)
        instance = self.app_class(**args)
        self.failUnlessEqual(want_url, instance.opts.root_url)

    def test_main_instantiates_server(self):
        """ main() should create a new server instance """
        params = self.valid_apps['simple']
        instance = params['instance']
        host = gracied.default_host
        port = gracied.default_port
        expect_stdout = """\
            Called GracieServer_class(
                (%(host)r, %(port)r),
                <Values at ...: {...}>)
            ...""" % vars()
        gracied.GracieServer = self.mock_server_class
        instance.main()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )
        self.failIfIs(instance.server, None)

    def test_main_sets_specified_socket_params(self):
        """ main() should set the server on the specified host:port """
        for key, params in self.iterate_params():
            instance = params['instance']
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
                    <Values at ...: {...}>)
                ...""" % vars()
            gracied.GracieServer = self.mock_server_class
            instance.main()
            self.failUnlessOutputCheckerMatch(
                expect_stdout, self.stdout_test.getvalue()
                )
            self.stdout_test.truncate(0)

    def test_main_calls_become_daemon(self):
        """ main() should attempt to become a daemon """
        params = self.valid_apps['simple']
        instance = params['instance']
        gracied.become_daemon = Mock('become_daemon')
        expect_stdout = """\
            Called become_daemon()
            """
        instance.main()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )

    def test_main_starts_server(self):
        """ main() should start GracieServer if child fork """
        params = self.valid_apps['simple']
        instance = params['instance']
        port = gracied.default_port
        expect_stdout = """\
            ...
            Called GracieServer.serve_forever()
            """
        gracied.GracieServer = self.mock_server_class
        instance.main()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue()
            )


class Test_ProgramMain(scaffold.Test_ProgramMain):
    """ Test cases for module __main__ function """

    def setUp(self):
        """ Set up test fixtures """
        self.program_module = gracied
        self.application_class = gracied.Gracie
        super(Test_ProgramMain, self).setUp()


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
