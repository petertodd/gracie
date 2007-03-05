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
import os
import sys
import textwrap
from minimock import Mock

test_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.dirname(test_dir)
if not test_dir in sys.path:
    sys.path.insert(1, test_dir)
if not code_dir in sys.path:
    sys.path.insert(1, code_dir)


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
        self.failUnlessEqual(True,
            checker.check_output(want, got, doctest.ELLIPSIS),
            "Expected %(want)r, got %(got)r:\n%(got)s" % locals()
        )


class Test_Exception(TestCase):
    """ Test cases for exception classes """

    def __init__(self, *args, **kwargs):
        """ Set up a new instance """
        self.valid_exceptions = NotImplemented
        unittest.TestCase.__init__(self, *args, **kwargs)

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
            self.failUnless(params['instance'])

    def test_exception_types(self):
        """ Exception instances should match expected types """
        for key, params in self.iterate_params():
            instance = params['instance']
            for match_type in params['types']:
                self.failUnless(isinstance(instance, match_type))
