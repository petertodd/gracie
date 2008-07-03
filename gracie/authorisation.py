# -*- coding: utf-8 -*-

# gracie/authorisation.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Behaviour for authorisation of OpenID requests
"""

import logging

# Get the Python logging instance for this module
_logger = logging.getLogger("gracie.authorisation")


class ConsumerAuthStore(object):
    """ Storage for consumer request authorisations """

    def __init__(self):
        """ Set up a new instance """
        self._authorisations = dict()

    def is_authorised(self, auth_tuple):
        """ Report authorisation of an (identity, known_root) tuple """
        is_authorised = self._authorisations.get(
            auth_tuple, False)
        return is_authorised

    def store_authorisation(self, auth_tuple, status):
        """ Store an authorisation status """
        self._authorisations[auth_tuple] = status

    def remove_authorisation(self, auth_tuple):
        """ Remove an authorisation status """
        if auth_tuple in self._authorisations:
            del self._authorisations[auth_tuple]

