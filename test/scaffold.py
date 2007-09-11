# -*- coding: utf-8 -*-

# scaffold.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Scaffolding for unit test modules
"""

import unittest
import doctest
import logging
import os
import sys
import textwrap
from StringIO import StringIO
from minimock import Mock

test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
if not test_dir in sys.path:
    sys.path.insert(1, test_dir)
if not parent_dir in sys.path:
    sys.path.insert(1, parent_dir)
bin_dir = os.path.join(parent_dir, "bin")

# Disable all but the most critical logging messages
logging.disable(logging.CRITICAL)


def suite(module_name):
    """ Create the test suite for named module """
    from sys import modules
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(modules[module_name])
    return suite

def unittest_main(argv=None):
    """ Mainline function for each unit test module """

    from sys import argv as sys_argv
    if not argv:
        argv = sys_argv

    exitcode = None
    try:
        unittest.main(argv=argv, defaultTest='suite')
    except SystemExit, e:
        exitcode = e.code

    return exitcode


def make_module_from_file(module_name, file_name):
    """ Make a new module object from the code in specified file """

    from types import ModuleType
    module = ModuleType(module_name)

    module_file = open(file_name, 'r')
    exec module_file in module.__dict__

    return module


def make_params_iterator(default_params_dict):
    """ Make a function for generating test parameters """

    def iterate_params(params_dict=None):
        """ Iterate a single test for a set of parameters """
        if not params_dict:
            params_dict = default_params_dict
        for key, params in params_dict.items():
            yield key, params

    return iterate_params


class TestCase(unittest.TestCase):
    """ Test case behaviour """

    def failUnlessOutputCheckerMatch(self, want, got):
        """ Fail the test unless output matches via doctest OutputChecker """
        checker = doctest.OutputChecker()
        want = textwrap.dedent(want)
        got = textwrap.dedent(got)
        self.failUnlessEqual(True,
            checker.check_output(want, got, doctest.ELLIPSIS),
            "Expected %(want)r, got %(got)r:"
            "\n--- want: ---\n%(want)s"
            "\n--- got: ---\n%(got)s" % locals()
        )


class Test_Exception(TestCase):
    """ Test cases for exception classes """

    def __init__(self, *args, **kwargs):
        """ Set up a new instance """
        self.valid_exceptions = NotImplemented
        super(Test_Exception, self).__init__(*args, **kwargs)

    def setUp(self):
        """ Set up test fixtures """
        for exc_type, params in self.valid_exceptions.items():
            args = (None,) * params['min_args']
            instance = exc_type(*args)
            self.valid_exceptions[exc_type]['instance'] = instance

        self.iterate_params = make_params_iterator(
            default_params_dict = self.valid_exceptions
        )

    def test_exception_instance(self):
        """ Exception instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_exception_types(self):
        """ Exception instances should match expected types """
        for key, params in self.iterate_params():
            instance = params['instance']
            for match_type in params['types']:
                match_type_name = match_type.__name__
                self.failUnless(isinstance(instance, match_type),
                    "%(instance)r is not an instance of %(match_type_name)s"
                        % locals()
                )


class Test_ProgramMain(TestCase):
    """ Test cases for program __main__ function

    Tests a module-level function named __main__ with behaviour
    inspired by Guido van Rossum's post "Python main() functions"
    <URL:http://www.artima.com/weblogs/viewpost.jsp?thread=4829>.
    
    It expects:
      * the program module has a __main__ function, that:
          * accepts an 'argv' argument, defaulting to sys.argv
          * instantiates a program application class
          * calls the application's main() method, passing argv
          * catches SystemExit and returns the error code
      * the application behaviour is defined in a class, that:
          * has an __init__() method accepting an 'argv' argument as
            the commandline argument list to parse
          * has a main() method responsible for running the program,
            and returning on successful program completion
          * raises SystemExit when an abnormal exit is required
    """

    def __init__(self, *args, **kwargs):
        """ Set up a new instance """
        self.program_module = NotImplemented
        self.application_class = NotImplemented
        super(Test_ProgramMain, self).__init__(*args, **kwargs)

    def setUp(self):
        """ Set up test fixtures """
        self.sys_argv_prev = sys.argv
        self.stdout_prev = sys.stdout
        self.stdout_test = StringIO()
        sys.stdout = self.stdout_test
        self.app_class_prev = self.application_class

        self.app_class_name = self.application_class.__name__
        self.mock_app = Mock(self.app_class_name)
        self.mock_app_class = Mock("%s_class" % self.app_class_name)
        self.mock_app_class.mock_returns = self.mock_app
        setattr(self.program_module,
            self.app_class_name, self.mock_app_class)

    def tearDown(self):
        """ Tear down test fixtures """
        sys.argv = self.sys_argv_prev
        sys.stdout = self.stdout_prev
        setattr(self.program_module,
            self.app_class_name, self.app_class_prev)

    def test_main_should_instantiate_app(self):
        """ __main__() should instantiate application class """
        app_class_name = self.app_class_name
        argv = ["foo", "bar"]
        expect_stdout = """\
            Called %(app_class_name)s_class(%(argv)r)...
            """ % locals()
        self.program_module.__main__(argv)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue())

    def test_main_should_call_app_main(self):
        """ __main__() should call the application main method """
        argv = ["foo", "bar"]
        app_class_name = self.app_class_name
        expect_stdout = """\
            Called %(app_class_name)s_class(%(argv)r)
            Called %(app_class_name)s.main()
            """ % locals()
        self.program_module.__main__(argv)
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue())

    def test_main_no_argv_should_supply_sys_argv(self):
        """ __main__() with no argv should supply sys.argv to application """
        sys_argv_test = ["foo", "bar"]
        sys.argv = sys_argv_test
        app_class_name = self.app_class_name
        expect_stdout = """\
            Called %(app_class_name)s_class(%(sys_argv_test)r)
            Called %(app_class_name)s.main()
            """ % locals()
        self.program_module.__main__()
        self.failUnlessOutputCheckerMatch(
            expect_stdout, self.stdout_test.getvalue())

    def test_main_should_return_none_on_success(self):
        """ __main__() should return None when no SystemExit raised """
        expect_exit_code = None
        exit_code = self.program_module.__main__()
        self.failUnlessEqual(expect_exit_code, exit_code)

    def test_main_should_return_exit_code_on_system_exit(self):
        """ __main__() should return application SystemExit code """
        expect_exit_code = object()
        def raise_system_exit(*args, **kwargs):
            raise SystemExit(expect_exit_code)
        self.mock_app.main = raise_system_exit
        exit_code = self.program_module.__main__()
        self.failUnlessEqual(expect_exit_code, exit_code)

