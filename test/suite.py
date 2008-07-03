#! /usr/bin/python
# -*- coding: utf-8 -*-

# test/suite.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test suite for the application modules
"""

import unittest
import sys
import os

import scaffold


def get_python_modules(file_list, file_suffix = '.py'):
    """ Return a list of module names from a filename list """
    python_modules = [m[:m.rfind(file_suffix)] for m in file_list
        if m.endswith(file_suffix)]
    return python_modules

def get_test_modules(module_list, module_prefix = 'test_'):
    """ Return the list of modules that are named as test modules """
    test_modules = [m for m in module_list
        if m.startswith(module_prefix)]
    return test_modules


def suite():
    """ Create the test suite for this module """
    loader = unittest.TestLoader()
    python_modules = get_python_modules(os.listdir(scaffold.test_dir))
    module_list = get_test_modules(python_modules)
    suite = loader.loadTestsFromNames(module_list)

    return suite


def __main__(argv=None):
    """ Mainline function for this module """
    from sys import argv as sys_argv
    if not argv:
        argv = sys_argv

    exitcode = None
    try:
        unittest.main(argv=argv, defaultTest='suite')
    except SystemExit, e:
        exitcode = e.code

    return exitcode

if __name__ == '__main__':
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
