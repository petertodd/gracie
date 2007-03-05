# -*- coding: utf-8 -*-

# http_response.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Utility module for HTTP response handling
"""


class HTTPResponseCodes(object):
    ok = 200
    
    moved_permanently = 301
    found = 302
    
    bad_request = 400
    unauthorized = 401
    forbidden = 403
    not_found = 404

    internal_server_error = 500
    not_implemented = 501
    service_unavailable = 503
