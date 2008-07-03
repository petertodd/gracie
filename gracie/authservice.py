# -*- coding: utf-8 -*-

# gracie/authservice.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Authentication services interface
"""

import pwd
import PAM
import logging

_logger = logging.getLogger("gracie.auth")

pam_service_name = "gracie"


class AuthenticationError(EnvironmentError):
    """ Raised when an authentication request fails """

    def __init__(self, code, reason):
        """ Set up a new instance """
        EnvironmentError.__init__(self, code, reason)


class BaseAuthService(object):
    """ Abstract interface to an authentication service """

    # Name of the auth service
    name = NotImplemented

    def get_entry(self, value):
        """ Get an entry from the service by key value """
        raise NotImplementedError

    def authenticate(self, credentials):
        """ Verify credentials against authentication service """
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


class _PamConversation(object):
    """ PAM authentication conversation """

    def __init__(self, password):
        """ Set up a new instance """
        self.password = password

    def __call__(self, auth, query_list, user_data):
        """ Callback from PAM system """
        _logger.info("PAM: received query")

        response_map = {
            PAM.PAM_PROMPT_ECHO_ON: (self.password, 0),
            PAM.PAM_PROMPT_ECHO_OFF: (self.password, 0),
            PAM.PAM_ERROR_MSG: ('', 0),
            PAM.PAM_TEXT_INFO: ('', 0),
            }
        pam_password_prompts = [
            PAM.PAM_PROMPT_ECHO_ON, PAM.PAM_PROMPT_ECHO_OFF,
            ]

        response_list = []
        for query, qtype in query_list:
            _logger.info(
                "PAM query: type %(qtype)r, %(query)r" % vars())
            response = response_map.get(qtype)
            if response is None:
                _logger.warn(
                    "PAM: unknown query type %(qtype)r" % vars())
                response_list = None
                break
            else:
                sanitised_response = response
                if qtype in pam_password_prompts:
                    sanitised_response = ("<password>", 0)
                _logger.info(
                    "PAM response: sending %(sanitised_response)r"
                    % vars()
                    )
                response_list.append(response)
        return response_list

class PamAuthService(PosixAuthService):
    """ Interface to PAM authentication service """

    def __init__(self):
        """ Set up a new instance """
        super(PamAuthService, self).__init__()

        self._pam_auth = PAM.pam()

    def _authenticate_creds(self, username, password):
        """ Authenticate credentials against PAM """
        self._pam_auth.start(pam_service_name)
        self._pam_auth.set_item(PAM.PAM_USER, username)
        conversation = _PamConversation(password)
        self._pam_auth.set_item(PAM.PAM_CONV, conversation)

        flags = 0
        flags |= PAM.PAM_SILENT
        flags |= PAM.PAM_DISALLOW_NULL_AUTHTOK
        self._pam_auth.authenticate(flags)
        self._pam_auth.acct_mgmt()

        got_username = self._pam_auth.get_item(PAM.PAM_USER)
        return got_username

    def authenticate(self, credentials):
        """ Verify credentials against authentication service """
        username = credentials['username']
        password = credentials['password']
        _logger.info(
            "Attempting to authenticate credentials"
            " for %(username)r" % vars()
            )
        try:
            got_username = self._authenticate_creds(username, password)
        except PAM.error, e:
            if len(e.args) < 2:
                (reason, code) = (str(e), 0)
            else:
                (reason, code) = e.args
            raise AuthenticationError(code, reason)

        _logger.info(
            "Successful authentication for %(username)r"
            % vars()
            )
        return got_username

