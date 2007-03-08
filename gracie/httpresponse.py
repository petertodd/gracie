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


from BaseHTTPServer import BaseHTTPRequestHandler
response_map = BaseHTTPRequestHandler.responses

response_codes = dict()
for code, (reason, explain) in response_map.items():
    key = reason.lower().replace(" ", "_")
    response_codes[key] = code


class ResponseHeader(object):
    """ Encapsulation of an HTTP response header """

    def __init__(self, code, protocol="HTTP/1.0"):
        """ Set up a new instance """
        self.code = code
        self.protocol = protocol
        self.fields = []

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
