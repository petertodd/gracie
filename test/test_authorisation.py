#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test/test_authorisation.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for authorisation module
"""

import sys

import scaffold

from gracie import authorisation


class Test_ConsumerAuthStore(scaffold.TestCase):
    """ Test cases for ConsumerAuthStore class """

    def setUp(self):
        """ Set up test fixtures """
        self.store_class = authorisation.ConsumerAuthStore

    def test_instantiate(self):
        """ New ConsumerAuthStore instance should be created """
        instance = self.store_class()
        self.failIfIs(instance, None)

    def test_is_authorised_unknown_returns_false(self):
        """ is_authorised for unknown args should return False """
        instance = self.store_class()
        auth_tuple = ("bogus", "bogus")
        is_authorised = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(False, is_authorised)

    def test_store_authorisation_result_in_authorisation(self):
        """ store_authorisation should let is_authorised succeed """
        instance = self.store_class()
        identity = "/id/fred"
        trust_root = "http://example.com/"
        auth_tuple = (identity, trust_root)
        status = True
        instance.store_authorisation(auth_tuple, status)
        got_status = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(True, got_status)

    def test_remove_authorisation_unknown_should_succeed(self):
        """ remove_authorisation for unknown args should succeed """
        instance = self.store_class()
        auth_tuple = ("bogus", "bogus")
        instance.remove_authorisation(auth_tuple)
        is_authorised = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(False, is_authorised)

    def test_remove_authorisation_result_in_no_authorisation(self):
        """ remove_authorisation should make is_authorised return False """
        instance = self.store_class()
        identity = "/id/fred"
        trust_root = "http://example.com/"
        auth_tuple = (identity, trust_root)
        status = True
        instance.store_authorisation(auth_tuple, status)
        instance.remove_authorisation(auth_tuple)
        got_status = instance.is_authorised(auth_tuple)
        self.failUnlessEqual(False, got_status)


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
