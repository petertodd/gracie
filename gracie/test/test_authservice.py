#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test_authservice.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for authservice module
"""

import scaffold
from scaffold import Mock

import authservice


class Test_BaseAuthService(scaffold.TestCase):
    """ Test cases for AuthService class """

    def setUp(self):
        """ Set up test fixtures """

        self.service_class = authservice.BaseAuthService

    def test_instantiate(self):
        """ New BaseAuthService instance should be created """
        instance = self.service_class()
        self.failUnless(instance is not None)

    def test_name_is_not_implemented(self):
        """ BaseAuthService should have name NotImplemented """
        instance = self.service_class()
        self.failUnlessEqual(NotImplemented, instance.name)

    def test_get_entry_is_not_implemented(self):
        """ BaseAuthService should not implement get_entry() """
        instance = self.service_class()
        name = "foo"
        self.failUnlessRaises(NotImplementedError,
            instance.get_entry, name
        )


stub_entries = [
    dict(id=1000, name="fred", fullname="Fred Nurk"),
]

class Stub_AuthService(object):
    """ Stub class for AuthService classes """

    def get_entry(self, value):
        match = [e for e in stub_entries
                 if e['name'] == value]
        if not match:
            raise KeyError("No such entry for %(value)s" % locals())
        entry = match[0]
        return entry

class Stub_PwdModule(object):
    """ Stub class for a pwd module """

    _entries = [(e['name'], "*", e['id'], 500, e['fullname'],
                 "/home/"+e['name'], "/bin/sh")
                for e in stub_entries]

    _entries_by_name = dict([(e[0], e) for e in _entries])
    _entries_by_uid = dict([(e[2], e) for e in _entries])

    def getpwnam(self, name):
        """ Get an entry by account name """
        try:
            entry = self._entries_by_name[name]
        except KeyError:
            raise KeyError("name not found: %(name)s" % locals())
        return entry

    def getpwuid(self, uid):
        """ Get an entry by account ID """
        try:
            entry = self._entries_by_uid[uid]
        except KeyError:
            raise KeyError("uid not found: %(uid)s" % locals())
        return entry

class Test_PosixAuthService(scaffold.TestCase):
    """ Test cases for PosixAuthService class """

    def setUp(self):
        """ Set up test fixtures """

        self.service_class = authservice.PosixAuthService

    def test_instantiate(self):
        """ New PosixAuthService instance should be created """
        instance = self.service_class()
        self.failUnless(instance is not None)

    def test_get_entry_name_unknown_raises_keyerror(self):
        """ get_entry for a bogus name should raise KeyError """
        pwd_module_prev = authservice.pwd
        pwd_module = Stub_PwdModule()
        authservice.pwd = pwd_module
        instance = self.service_class()
        name = "nosuchuser"
        self.failUnlessRaises(KeyError,
            instance.get_entry, name
        )
        authservice.pwd = pwd_module_prev

    def test_get_entry_name_known_returns_entry(self):
        """ get_entry for a known name should return an auth entry """
        pwd_module_prev = authservice.pwd
        pwd_module = Stub_PwdModule()
        authservice.pwd = pwd_module
        instance = self.service_class()
        pwd_entry = pwd_module.getpwnam("fred")
        (name, _, uid, _, fullname, _, _) = pwd_entry
        expect_entry = dict(
            id = uid,
            name = name,
            fullname = fullname,
        )
        entry = instance.get_entry(name)
        self.failUnlessEqual(expect_entry, entry)
        authservice.pwd = pwd_module_prev


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
