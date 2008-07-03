# -*- coding: utf-8 -*-

# gracie/__init__.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Gracie - OpenID provider for local accounts

Gracie is an OpenID server (a "provider" in OpenID terminology) that
serves OpenID identities for the local system PAM accounts. It
authenticates users with a username/password challenge.

The OpenID protocol is documented at <URL:http://openid.net/>.
"""

import server

__version__ = server.__version__
__date__ = "2008-07-03"
__author_name__ = "Ben Finney"
__author_email__ = "ben+python@benfinney.id.au"
__author__ = "%s <%s>" % (__author_name__, __author_email__)
__copyright__ = "Copyright © %s %s" % (
    __date__.split('-')[0], __author_name__
    )
__license__ = "GPL"
__url__ = "http://trac.whitetree.org/gracie/"
