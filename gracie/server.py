# -*- coding: utf-8 -*-

# server.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Behaviour for OpenID provider server
"""


class OpenIDServer(object):
    """ Server for OpenID protocol requests """

    def __init__(self):
        """ Set up a new instance """

    def serve_forever(self):
        """ Serve requests endlessly """
