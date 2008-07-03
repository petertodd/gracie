# -*- coding: utf-8 -*-

# gracie/http_response.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Utility module for HTTP response handling
"""


# Map names to codes as per RFC2616
response_codes = {
    "OK": 200,
    "Found": 302,
    "Not Found": 404,
    "Internal Server Error": 500,
    }

content_type_xhtml = "application/xhtml+xml"


class ResponseHeader(object):
    """ Encapsulation of an HTTP response header """

    def __init__(
        self, code,
        protocol="HTTP/1.0", content_type=content_type_xhtml,
        ):
        """ Set up a new instance """
        self.code = code
        self.protocol = protocol
        self.fields = []
        self.fields.append(("Content-Type", content_type))

class Response(object):
    """ Encapsulation for an HTTP response """

    def __init__(self, header, data=None):
        """ Set up a new instance """
        self.header = header
        self.data = data

    def send_to_handler(self, handler):
        """ Send this response via a request handler """
        handler.send_response(self.header.code)
        for key, value in self.header.fields:
            handler.send_header(key, value)
        handler.end_headers()
        handler.wfile.write(self.data)
        handler.wfile.close()
