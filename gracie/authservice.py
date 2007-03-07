# -*- coding: utf-8 -*-

# authservice.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Authentication services interface
"""

import pwd


class BaseAuthService(object):
    """ Abstract interface to an authentication service """

    # Name of the auth service
    name = NotImplemented

    def get_entry(self, value):
        """ Get an entry from the service by key value """
        raise NotImplementedError


class PosixAuthService(BaseAuthService):
    """ Interface to POSIX authentication service """

    def _pwd_entry_to_auth_entry(self, pwd_entry):
        """ Construct an auth entry from a pwd entry """
        (name, _, uid, _, comment, _, _) = pwd_entry
        fullname = comment.split(",")[0]
        entry = dict(
            id=uid,
            name=name,
            fullname=fullname,
        )
        return entry

    def get_entry(self, value):
        """ Get an entry from the service by key value """
        pwd_entry = pwd.getpwnam(value)
        entry = self._pwd_entry_to_auth_entry(pwd_entry)
        return entry
