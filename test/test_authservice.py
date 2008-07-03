#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test/test_authservice.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for authservice module
"""

import scaffold

from gracie import authservice


class Test_ModuleExceptions(scaffold.Test_Exception):
    """ Test cases for module exceptions """

    def setUp(self):
        """ Set up test fixtures """
        self.valid_exceptions = {
            authservice.AuthenticationError: dict(
                min_args = 2,
                types = [EnvironmentError],
                ),
            }

        super(Test_ModuleExceptions, self).setUp()

    def test_autherror_string_contains_reason(self):
        """ AuthenticationError string should contain code and reason """
        code = 42
        reason = "Naughty!"
        instance = authservice.AuthenticationError(code, reason)
        str(instance)
        self.failUnlessOutputCheckerMatch(
            "...%(code)s..." % vars(), str(instance)
            )
        self.failUnlessOutputCheckerMatch(
            "...%(reason)s..." % vars(), str(instance)
            )


class Test_BaseAuthService(scaffold.TestCase):
    """ Test cases for AuthService class """

    def setUp(self):
        """ Set up test fixtures """

        self.service_class = authservice.BaseAuthService

    def test_instantiate(self):
        """ New BaseAuthService instance should be created """
        instance = self.service_class()
        self.failIfIs(instance, None)

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

    def test_authenticate_is_not_implemented(self):
        """ BaseAuthService should not implement authenticat() """
        instance = self.service_class()
        credentials = dict(
            username = "foo",
            password = "bar",
            )
        self.failUnlessRaises(
            NotImplementedError,
            instance.authenticate, credentials
            )


stub_entries = [
    dict(id=1000, name="fred", password="password1",
         fullname="Fred Nurk", comment="Fred Nurk"),
    dict(id=1010, name="bill", password="secret1",
         fullname="William Fosdycke", comment="William Fosdycke,,,"),
    ]

class Stub_AuthService(object):
    """ Stub class for AuthService classes """

    def get_entry(self, value):
        match = [e for e in stub_entries if e['name'] == value]
        if not match:
            raise KeyError("No entry for %(value)r" % vars())
        entry = match[0]
        return entry

    def authenticate(self, credentials):
        try:
            username = credentials['username']
            password = credentials['password']
            entry = self.get_entry(username)
        except KeyError, e:
            raise authservice.AuthenticationError(
                0, "User not found")
        if password != entry['password']:
            raise authservice.AuthenticationError(
                0, "Authentication failed")
        return username

class Stub_PwdModule(object):
    """ Stub class for a pwd module """

    _entries = [
        (e['name'], "*", e['id'], 500, e['comment'],
         "/home/"+e['name'], "/bin/sh")
        for e in stub_entries]

    _entries_by_name = dict([(e[0], e) for e in _entries])
    _entries_by_uid = dict([(e[2], e) for e in _entries])

    def getpwnam(self, name):
        """ Get an entry by account name """
        try:
            entry = self._entries_by_name[name]
        except KeyError:
            raise KeyError("name not found: %(name)s" % vars())
        return entry

    def getpwuid(self, uid):
        """ Get an entry by account ID """
        try:
            entry = self._entries_by_uid[uid]
        except KeyError:
            raise KeyError("uid not found: %(uid)s" % vars())
        return entry

class Test_PosixAuthService(scaffold.TestCase):
    """ Test cases for PosixAuthService class """

    def setUp(self):
        """ Set up test fixtures """

        self.service_class = authservice.PosixAuthService

        self.pwd_module_prev = authservice.pwd
        self.pwd_module = Stub_PwdModule()
        authservice.pwd = self.pwd_module

    def tearDown(self):
        """ Tear down test fixtures """
        authservice.pwd = self.pwd_module_prev

    def test_instantiate(self):
        """ New PosixAuthService instance should be created """
        instance = self.service_class()
        self.failIfIs(instance, None)

    def test_get_entry_name_unknown_raises_keyerror(self):
        """ get_entry for a bogus name should raise KeyError """
        instance = self.service_class()
        name = "nosuchuser"
        self.failUnlessRaises(
            KeyError,
            instance.get_entry, name
            )

    def test_get_entry_name_known_returns_entry(self):
        """ get_entry for a known name should return an auth entry """
        instance = self.service_class()
        pwd_entry = self.pwd_module.getpwnam("fred")
        (name, _, uid, _, fullname, _, _) = pwd_entry
        expect_entry = dict(
            id = uid,
            name = name,
            fullname = fullname,
            )
        entry = instance.get_entry(name)
        self.failUnlessEqual(expect_entry, entry)

    def test_get_entry_strips_extra_info_from_comment(self):
        """ get_entry should strip extra info to get the fullname """
        instance = self.service_class()
        pwd_entry = self.pwd_module.getpwnam("bill")
        (name, _, uid, _, comment, _, _) = pwd_entry
        fullname = comment.split(",")[0]
        expect_entry = dict(
            id = uid,
            name = name,
            fullname = fullname,
            )
        entry = instance.get_entry(name)
        self.failUnlessEqual(expect_entry, entry)


class Stub_PamError(Exception):
    def __init__(self, code, reason):
        Exception.__init__(self, reason, code)

class Stub_PamAuth(object):
    """ Stub class for PAM authentication service """

    _entries = dict((e['name'], e) for e in stub_entries)

    def start(self, service):
        self._items = dict()

    def get_item(self, key):
        return self._items[key]

    def set_item(self, key, value):
        self._items[key] = value

    def _converse(self, query_list):
        conversation = self._items[PAM.PAM_CONV]
        response_list = conversation(self, query_list, None)
        return response_list

    def _get_auth_entry(self, username):
        try:
            entry = self._entries[username]
        except KeyError:
            raise PAM.error(
                PAM.PAM_USER_UNKNOWN,
                "User %(username)s not found" % vars()
                )
        return entry

    def authenticate(self, flags=0):
        username = self._items[PAM.PAM_USER]
        entry = self._get_auth_entry(username)

        query_list = []
        query_list.append(("Password: ", PAM.PAM_PROMPT_ECHO_OFF))
        response_list = self._converse(query_list)

        auth_success = False
        if response_list is None:
            response_list = []
        for response, _ in response_list:
            if not len(response):
                continue
            password = response
            if password == entry['password']:
                query_list = [
                    ("Login successful", PAM.PAM_SUCCESS)
                    ]
                self._converse(query_list)
                auth_success = True

        if not auth_success:
            raise PAM.error(PAM.PAM_AUTH_ERR, "Authentication failed")

    def acct_mgmt(self): pass

class Stub_PamModule(object):
    """ Stub class for PAM authentication module """

    error = Stub_PamError

    [
        PAM_USER,
        PAM_CONV,
        PAM_SILENT,
        PAM_DISALLOW_NULL_AUTHTOK,
        PAM_PROMPT_ECHO_ON,
        PAM_PROMPT_ECHO_OFF,
        PAM_ERROR_MSG,
        PAM_TEXT_INFO,

        PAM_ABORT,
        PAM_AUTH_ERR,
        PAM_CRED_INSUFFICIENT,
        PAM_AUTHINFO_UNVAIL,
        PAM_MAXTRIES,
        PAM_USER_UNKNOWN,

        PAM_SUCCESS,
        ] = range(15)

    def pam(self):
        """ Return a handle to the authentication system """
        authenticator = Stub_PamAuth()
        return authenticator

stub_pam_module = Stub_PamModule()
PAM = stub_pam_module

class Test_PamAuthService(scaffold.TestCase):
    """ Test cases for PamAuthService class """

    def setUp(self):
        """ Set up test fixtures """

        self.service_class = authservice.PamAuthService

        self.pwd_module_prev = authservice.pwd
        self.pam_module_prev = authservice.PAM
        self.pwd_module = Stub_PwdModule()
        self.pam_module = stub_pam_module
        authservice.pwd = self.pwd_module
        authservice.PAM = self.pam_module

    def tearDown(self):
        """ Tear down test fixtures """
        authservice.pwd = self.pwd_module_prev
        authservice.PAM = self.pam_module_prev

    def test_instantiate(self):
        """ New PosixAuthService instance should be created """
        instance = self.service_class()
        self.failIfIs(instance, None)

    def test_authenticate_unknown_user_raises_autherror(self):
        """ Auth for unknown user should raise AuthenticationError """
        instance = self.service_class()
        credentials = dict(
            username = "bogus",
            password = "bogus",
            )
        self.failUnlessRaises(
            authservice.AuthenticationError,
            instance.authenticate, credentials
            )

    def test_authenticate_bad_creds_returns_false(self):
        """ Auth for bad credentials should raise AuthenticationError """
        instance = self.service_class()
        credentials = dict(
            username = "fred",
            password = "bogus",
            )
        self.failUnlessRaises(
            authservice.AuthenticationError,
            instance.authenticate, credentials
            )

    def test_authenticate_good_creds_returns_username(self):
        """ Authentication for good credentials should return username """
        instance = self.service_class()
        credentials = dict(
            username = "fred",
            password = "password1",
            )
        username = credentials['username']
        result = instance.authenticate(credentials)
        self.failUnlessEqual(username, result)


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
