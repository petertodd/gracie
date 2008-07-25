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

_version = server.__version__
_date = "2008-07-25"
_author_name = "Ben Finney"
_author_email = "ben+python@benfinney.id.au"
_author = "%(_author_name)s <%(_author_email)s>" % vars()
_copyright_year_begin = "2007"
_copyright_year = _date.split('-')[0]
_copyright_year_range = _copyright_year_begin
if _copyright_year > _copyright_year_begin:
    _copyright_year_range += "..%(_copyright_year)s" % vars()
_copyright = "Copyright © %(_copyright_year_range)s %(_author)s" % vars()
_license = "GPL"
_url = "http://trac.whitetree.org/gracie/"
