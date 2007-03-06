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


class ResponseHeader(object):
    """ Encapsulation of an HTTP response header """

    def __init__(self, code, message=None, protocol="HTTP/1.0"):
        """ Set up a new instance """
        self.code = code
        self.message = message
        self.protocol = protocol
        self.fields = dict()

        self.fields.update({
            'Date': None,
            'Content-Type': "text/html",
        })

class Response(object):
    """ Encapsulation for an HTTP response """

    def __init__(self, header):
        """ Set up a new instance """
        self.header = header
