#! /usr/bin/env python
# -*- coding: utf-8 -*-

# test_page.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for page module
"""

from string import Template
import textwrap

import scaffold
from scaffold import Mock

import page


class Test_Page(scaffold.TestCase):
    """ Test cases for Page class """

    def setUp(self):
        """ Set up test fixtures """

        self.page_class = page.Page

        page.page_template = Template(
            textwrap.dedent("""\
            Page {
                Coding: $character_encoding
                Title: $page_title
                $page_body
            }""")
        )

        page.body_template = Template(
            textwrap.dedent("""\
            Body {
                Title: $page_title
                Content: $page_content
            }""")
        )

        self.valid_pages = {
            'simple': dict(
            ),
            'welcome': dict(
                title = "Welcome",
                content = "Lorem ipsum dolor sic amet",
            ),
            'result': dict(
                title = "Result",
                content = "Here is your result: $result.",
                values = dict(
                    result = "thribble",
                ),
            ),
        }

        for key, params in self.valid_pages.items():
            args = params.get('args')
            if args is None:
                args = dict()
            title = params.get('title')
            if title is not None:
                args.update(dict(title=title))
            params['args'] = args
            instance = self.page_class(**args)
            content = params.get('content')
            if content is not None:
                instance.content = content
            values = params.get('values')
            if values is not None:
                instance.values = values
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_pages
        )

    def test_instantiate(self):
        """ New Page instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failUnless(instance is not None)

    def test_title_as_specified(self):
        """ Page title should be as specified """
        for key, params in self.iterate_params():
            title = params.get('title')
            if not title:
                continue
            instance = params['instance']
            self.failUnlessEqual(title, instance.title)

    def test_serialise_uses_template(self):
        """ Page.serialise should use provided template """
        params = self.valid_pages['welcome']
        instance = params['instance']
        expect_data = """\
            Page {
                Coding: utf-8
                Title: %(title)s
                Body {
                Title: %(title)s
                Content: %(content)s
            }
            }""" % params
        page_data = instance.serialise()
        self.failUnlessOutputCheckerMatch(expect_data, page_data)

    def test_serialise_substitutes_values(self):
        """ Page.serialise should substitute values into template """
        params = self.valid_pages['result']
        instance = params['instance']
        content = params['content']
        values = params['values']
        expect_content = Template(content).substitute(values)
        params['expect_content'] = expect_content
        expect_data = """\
            Page {
                Coding: utf-8
                Title: %(title)s
                Body {
                Title: %(title)s
                Content: %(expect_content)s
            }
            }""" % params
        page_data = instance.serialise()
        self.failUnlessOutputCheckerMatch(expect_data, page_data)


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
