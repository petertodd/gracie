#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test_httpresponse.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for httpresponse module
"""

import scaffold
from scaffold import Mock

import httpresponse


class Test_ResponseHeader(scaffold.TestCase):
    """ Test cases for ResponseHeader class """

    def setUp(self):
        """ Set up test fixtures """

        self.header_class = httpresponse.ResponseHeader

        self.valid_headers = {
            'simple': dict(
                code = 200,
            ),
            'ok-message': dict(
                code = 200,
                message = "Daijoubu",
            ),
            'ok-protocol': dict(
                code = 200,
                protocol = "HTTP/1.1",
            ),
        }

        for key, params in self.valid_headers.items():
            args = params.get('args', dict())
            code = params['code']
            args['code'] = code
            message = params.get('message')
            if message is not None:
                args['message'] = message
            protocol = params.get('protocol')
            if protocol is not None:
                args['protocol'] = protocol
            params['args'] = args
            instance = self.header_class(**args)
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_headers
        )

    def test_initialise(self):
        """ New ResponseHeader instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_code_as_specified(self):
        """ ResponseHeader should have specified status code """
        for key, params in self.iterate_params():
            code = params['code']
            instance = params['instance']
            self.failUnlessEqual(code, instance.code)

    def test_message_as_specified(self):
        """ ResponseHeader should have specified status message """
        for key, params in self.iterate_params():
            message = params.get('message')
            if message is None:
                continue
            instance = params['instance']
            self.failUnlessEqual(message, instance.message)

    def test_protocol_default_http_1_0(self):
        """ ResponseHeader protocol should default to HTTP/1.0 """
        params = self.valid_headers['simple']
        instance = params['instance']
        protocol = "HTTP/1.0"
        self.failUnlessEqual(protocol, instance.protocol)

    def test_protocol_as_specified(self):
        """ ResponseHeader should have specified response protocol """
        for key, params in self.iterate_params():
            protocol = params.get('protocol')
            if protocol is None:
                continue
            instance = params['instance']
            self.failUnlessEqual(protocol, instance.protocol)

    def test_fields_should_be_populated(self):
        """ New ResponseHeader fields should be populated """
        expect_fields = {
            'Content-Type': "text/html",
            'Date': None,
        }
        for key, params in self.iterate_params():
            instance = params['instance']
            for field_key, field_value in expect_fields.items():
                if field_value is None:
                    self.failUnless(field_key in instance.fields,
                        "Expected field %(field_key)r not in header"
                            % locals()
                    )
                else:
                    fields = instance.fields
                    value = fields[field_key]
                    self.failUnlessEqual(
                        field_value, instance.fields[field_key],
                        "Header field %(field_key)r should have value"
                        " %(field_value)r, not %(value)r" % locals()
                    )


class Stub_ResponseHeader(object):
    """ Stub class for response header """

    def __init__(self, code, message=None, protocol=None):
        self.code = code
        self.message = message
        self.protocol = protocol
        self.fields = dict()

class Test_Response(scaffold.TestCase):
    """ Test cases for Response class """

    def setUp(self):
        """ Set up test fixtures """

        self.response_class = httpresponse.Response

        self.valid_responses = {
            'simple': dict(
                header = Stub_ResponseHeader(code = 200),
            ),
        }

        for key, params in self.valid_responses.items():
            args = params.get('args', dict())
            header = params['header']
            args['header'] = header
            params['args'] = args
            instance = self.response_class(**args)
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_responses
        )

    def test_initialise(self):
        """ New Response instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_header_as_specified(self):
        """ Response should have specified header """
        for key, params in self.iterate_params():
            header = params['header']
            instance = params['instance']
            self.failUnlessEqual(header, instance.header)


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
