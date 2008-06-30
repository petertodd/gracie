# -*- coding: utf-8 -*-

# scaffold.py
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
import operator
import re
import textwrap
from StringIO import StringIO
from minimock import Mock
from minimock import (
    mock,
    restore as mock_restore,
)

test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
if not test_dir in sys.path:
    sys.path.insert(1, test_dir)
if not parent_dir in sys.path:
    sys.path.insert(1, parent_dir)
bin_dir = os.path.join(parent_dir, "bin")

# Disable all but the most critical logging messages
logging.disable(logging.CRITICAL)


class Container(object):
    """ Simple container class for attributes """


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


def normalise_function_parameters(text):
    """ Return a version of ``text`` with function parameters normalised

        The normalisations performed are:

        * Remove any whitespace sequence between an opening
          parenthesis '(' and a subsequent non-whitespace character.

        * Remove any whitespace sequence between a non-whitespace
          character and a closing parenthesis ')'.

        * Ensure a comma ',' and a subsequent non-whitespace character
          are separated by a single space ' '.

        """
    normalised_text = text
    normalise_map = {
        re.compile(r"\(\s+(\S)"): r"(\1",
        re.compile(r"(\S)\s+\)"): r"\1)",
        re.compile(r",\s*(\S)"): r", \1",
        }
    for search_pattern, replace_pattern in normalise_map.items():
        normalised_text = re.sub(
            search_pattern, replace_pattern, normalised_text)

    return normalised_text

doctest.NORMALIZE_FUNCTION_PARAMETERS = (
    doctest.register_optionflag('NORMALIZE_FUNCTION_PARAMETERS'))

class MinimockOutputChecker(doctest.OutputChecker, object):
    """ Class for matching output of MiniMock objects against expectations """

    def check_output(self, want, got, optionflags):
        if (optionflags & doctest.NORMALIZE_FUNCTION_PARAMETERS):
            want = normalise_function_parameters(want)
            got = normalise_function_parameters(got)
        output_match = super(MinimockOutputChecker, self).check_output(
            want, got, optionflags)
        return output_match
    check_output.__doc__ = doctest.OutputChecker.check_output.__doc__


class TestCase(unittest.TestCase):
    """ Test case behaviour """

    def failUnlessRaises(self, exc_class, func, *args, **kwargs):
        """ Fail if the function call does not raise the specified exception
        class """
        try:
            super(TestCase, self).failUnlessRaises(exc_class, func, *args, **kwargs)
        except self.failureException:
            exc_class_name = exc_class.__name__
            msg = ("Exception %(exc_class_name)s not raised"
                " for function call: args=%(args)r kwargs=%(kwargs)r"
            ) % locals()
            raise self.failureException(msg)


    def failIfIs(self, first, second, msg=None):
        """ Fail if the two objects are identical as determined by the
            'is' operator
        """
        if first is second:
            if msg is None:
                msg = "%(first)r is %(second)r" % locals()
            raise self.failureException(msg)

    def failUnlessIs(self, first, second, msg=None):
        """ Fail unless the two objects are identical as determined by
            the 'is' operator
        """
        if first is not second:
            if msg is None:
                msg = "%(first)r is not %(second)r" % locals()
            raise self.failureException(msg)

    assertIs = failUnlessIs
    assertNotIs = failIfIs

    def failIfIn(self, first, second, msg=None):
        """ Fail if the second object is contained by the first,
        as determined by the 'in' operator
        """
        if second in first:
            if msg is None:
                msg = "%(second)r is in %(first)r" % locals()
            raise self.failureException(msg)

    def failUnlessIn(self, first, second, msg=None):
        """ Fail unless the second object is contained by the first,
        as determined by the 'in' operator
        """
        if second not in first:
            if msg is None:
                msg = "%(second)r is not in %(first)r" % locals()
            raise self.failureException(msg)

    assertIn = failUnlessIn
    assertNotIn = failIfIn

    def failUnlessOutputCheckerMatch(self, want, got, msg=None):
        """ Fail unless the specified string matches the expected

            Fail the test unless ``want`` matches ``got``, as
            determined by a ``MinimockOutputChecker`` instance. This
            is not an equality check, but a pattern match according to
            the MinimockOutputChecker rules.

            """
        checker = MinimockOutputChecker()
        want = textwrap.dedent(want)
        source = ""
        example = doctest.Example(source, want)
        got = textwrap.dedent(got)
        checker_optionflags = reduce(operator.or_, [
            doctest.ELLIPSIS,
            doctest.NORMALIZE_FUNCTION_PARAMETERS,
            ])
        if not checker.check_output(want, got, checker_optionflags):
            if msg is None:
                diff = checker.output_difference(
                    example, got, checker_optionflags)
                msg = "\n".join([
                    "Output received did not match expected output",
                    "%(diff)s",
                    ]) % vars()
            raise self.failureException(msg)

    assertOutputCheckerMatch = failUnlessOutputCheckerMatch

    def failIfIsInstance(self, obj, classes):
        """ Fail if the object 'obj' is an instance of any of 'classes' """
        if isinstance(obj, classes):
            msg = "%(obj)r is an instance of one of %(classes)r" % locals()
            raise self.failureException(msg)

    def failUnlessIsInstance(self, obj, classes):
        """ Fail if the object 'obj' is not an instance of any of 'classes' """
        if not isinstance(obj, classes):
            msg = "%(obj)r is not an instance of any of %(classes)r" % locals()
            raise self.failureException(msg)

    assertIsInstance = failUnlessIsInstance
    assertNotIsInstance = failIfIsInstance


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
            params['args'] = args
            instance = exc_type(*args)
            params['instance'] = instance

        self.iterate_params = make_params_iterator(
            default_params_dict = self.valid_exceptions
        )

    def test_exception_instance(self):
        """ Exception instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failIfIs(None, instance)

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
        self.mock_outfile = StringIO()

        self.app_class_name = self.application_class.__name__
        self.mock_app = Mock("test_app", outfile=self.mock_outfile)
        self.mock_app_class = Mock(self.app_class_name,
            outfile=self.mock_outfile)
        self.mock_app_class.mock_returns = self.mock_app
        mock(self.app_class_name, mock_obj=self.mock_app_class,
            nsdicts=[self.program_module.__dict__])

    def tearDown(self):
        """ Tear down test fixtures """
        mock_restore()

    def test_main_should_instantiate_app(self):
        """ __main__() should instantiate application class """
        app_class_name = self.app_class_name
        argv = ["foo", "bar"]
        expect_mock_output = """\
            Called %(app_class_name)s(%(argv)r)...
            """ % locals()
        self.program_module.__main__(argv)
        self.failUnlessOutputCheckerMatch(
            expect_mock_output, self.mock_outfile.getvalue())

    def test_main_should_call_app_main(self):
        """ __main__() should call the application main method """
        argv = ["foo", "bar"]
        app_class_name = self.app_class_name
        expect_mock_output = """\
            Called %(app_class_name)s(%(argv)r)
            Called test_app.main()
            """ % locals()
        self.program_module.__main__(argv)
        self.failUnlessOutputCheckerMatch(
            expect_mock_output, self.mock_outfile.getvalue())

    def test_main_no_argv_should_supply_sys_argv(self):
        """ __main__() with no argv should supply sys.argv to application """
        sys_argv_test = ["foo", "bar"]
        mock("sys.argv", mock_obj=sys_argv_test)
        app_class_name = self.app_class_name
        expect_mock_output = """\
            Called %(app_class_name)s(%(sys_argv_test)r)
            Called test_app.main()
            """ % locals()
        self.program_module.__main__()
        self.failUnlessOutputCheckerMatch(
            expect_mock_output, self.mock_outfile.getvalue())

    def test_main_should_return_none_on_success(self):
        """ __main__() should return None when no SystemExit raised """
        expect_exit_code = None
        exit_code = self.program_module.__main__()
        self.failUnlessEqual(expect_exit_code, exit_code)

    def test_main_should_return_exit_code_on_system_exit(self):
        """ __main__() should return application SystemExit code """
        expect_exit_code = object()
        self.mock_app.main.mock_raises = SystemExit(expect_exit_code)
        exit_code = self.program_module.__main__()
        self.failUnlessEqual(expect_exit_code, exit_code)

