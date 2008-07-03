#! /usr/bin/python
# -*- coding: utf-8 -*-

# test/test_pagetemplate.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Unit test for pagetemplate module
"""

from string import Template
import textwrap

import scaffold

from gracie import pagetemplate


class Mixin_PageTemplateFixture(object):
    """ Mix-in class for page template fixtures """

    def setUp(self):
        """ Set up test fixtures """

        pagetemplate.page_template = Template(
            textwrap.dedent("""\
                Page {
                    Coding: $character_encoding
                    Title: $page_title
                    $page_body
                }""")
            )

        pagetemplate.body_template = Template(
            textwrap.dedent("""\
                Body {
                    Title: $page_title
                    Auth entry: $auth_entry
                    Content: $page_content
                }""")
            )

    def tearDown(self):
        """ Tear down test fixtures """


class Test_Page(
    scaffold.TestCase,
    Mixin_PageTemplateFixture):
    """ Test cases for Page class """

    def setUp(self):
        """ Set up test fixtures """

        self.page_class = pagetemplate.Page

        Mixin_PageTemplateFixture.setUp(self)

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
            'authenticated': dict(
                title = "Logged in",
                content = "Lorem ipsum dolor sic amet",
                auth_entry = dict(
                    id = 1010,
                    name = "fred",
                    fullname = "Fred Nurk",
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
            values = params.get('values', dict())
            if 'auth_entry' not in values:
                values.update({'auth_entry': None})
            values.update(dict(
                server_version = "FooBar v0.0",
                server_location = "frobnitz:9779",
                root_url = "/",
                server_url = "/openidserver",
                login_url = "/login",
                logout_url = "/logout",
                ))
            instance.values.update(values)
            params['instance'] = instance

        self.iterate_params = scaffold.make_params_iterator(
            default_params_dict = self.valid_pages
            )

    def test_instantiate(self):
        """ New Page instance should be created """
        for key, params in self.iterate_params():
            instance = params['instance']
            self.failIfIs(None, instance)

    def test_title_as_specified(self):
        """ Page title should be as specified """
        for key, params in self.iterate_params():
            title = params.get('title')
            if not title:
                continue
            instance = params['instance']
            self.failUnlessEqual(title, instance.title)

    def test_values_as_specified(self):
        """ Page values should be as specified """
        for key, params in self.iterate_params():
            values = params.get('values')
            if not values:
                continue
            instance = params['instance']
            self.failUnlessEqual(values, instance.values)

    def test_serialise_uses_template(self):
        """ Page.serialise should use provided template """
        params = self.valid_pages['welcome']
        instance = params['instance']
        expect_data = """\
            Page {
                Coding: ...
                Title: ...
                Body {
                Title: ...
                Auth entry: ...
                Content: ...
            }
            }"""
        page_data = instance.serialise()
        self.failUnlessOutputCheckerMatch(expect_data, page_data)

    def test_serialise_substitutes_values(self):
        """ Page.serialise should substitute values into template """
        params = self.valid_pages['result']
        instance = params['instance']
        title = params['title']
        content = params['content']
        values = params['values']
        auth_entry = values['auth_entry']
        expect_content = Template(content).substitute(values)
        expect_data = """\
            Page {
                Coding: utf-8
                Title: %(title)s
                Body {
                Title: %(title)s
                Auth entry: %(auth_entry)s
                Content: %(expect_content)s
            }
            }""" % vars()
        page_data = instance.serialise()
        self.failUnlessOutputCheckerMatch(expect_data, page_data)


class Test_PageTemplates(scaffold.TestCase):
    """ Test cases for individual page templates """

    def test_internal_error_page_contains_message(self):
        """ Internal Error page should contain specified message """
        message = "Bad stuff happened"
        page = pagetemplate.internal_error_page(message)
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "Page {...%(message)s...}" % vars(), page_data
            )

    def test_url_not_found_page_contains_url(self):
        """ Resulting page should contain the referent URL """
        url = "/flim/flam/flom"
        page = pagetemplate.url_not_found_page(url)
        expect_data = "...%(url)s..." % vars()
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(expect_data, page_data)

    def test_protocol_error_page_contains_message(self):
        """ Protocol Error page should contain specified message """
        message = "Bad stuff happened"
        page = pagetemplate.protocol_error_page(message)
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "Page {...%(message)s...}" % vars(), page_data
            )

    def test_about_site_page_returns_page(self):
        """ About Site page should return page """
        page = pagetemplate.about_site_view_page()
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "Page {...}", page_data
            )

    def test_identity_user_not_found_page_contains_name(self):
        """ Resulting page should contain the referent user name """
        name = "fred"
        page = pagetemplate.identity_user_not_found_page(name)
        expect_data = "...%(name)s..." % vars()
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(expect_data, page_data)

    def test_identity_view_user_page_contains_name(self):
        """ Resulting page should contain the referent user name """
        entry = dict(
            id = 9999,
            name = "fred",
            fullname = "Fred Nurk",
            )
        identity_url = "http://example.org/id/%(name)s" % entry
        server_url = "http://example.org/openidserver"
        page = pagetemplate.identity_view_user_page(
            entry, identity_url
            )
        page.values.update(dict(server_url=server_url))
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "...%(id)s..." % entry, page_data
            )
        self.failUnlessOutputCheckerMatch(
            "...%(name)s..." % entry, page_data
            )
        self.failUnlessOutputCheckerMatch(
            "...%(fullname)s..." % entry, page_data
            )
        self.failUnlessOutputCheckerMatch(
            "...%(identity_url)s..." % vars(), page_data
            )

    def test_login_user_not_found_page_contains_name(self):
        """ Resulting page should contain the referent user name """
        name = "bogus"
        page = pagetemplate.login_user_not_found_page(name)
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "...%(name)s..." % vars(), page_data
            )

    def test_login_view_page_returns_page(self):
        """ View login should return page """
        page = pagetemplate.login_view_page()
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "Page {...}", page_data
            )

    def test_login_cancel_returns_page(self):
        """ Cancel login should return page """
        page = pagetemplate.login_cancelled_page()
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "Page {...}", page_data
            )

    def test_login_submit_failed_page_contains_details(self):
        """ Resulting page should contain specified details """
        message = "Did gyre and gimble in the wabe"
        name = "fred"
        page = pagetemplate.login_submit_failed_page(message, name)
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "...%(message)s..." % vars(), page_data
            )
        self.failUnlessOutputCheckerMatch(
            "...%(name)s..." % vars(), page_data
            )

    def test_wrong_authentication_page_contains_url(self):
        """ Resulting page should contain the specified URLs """
        want_username = "bill"
        want_id = "http://foo.example.org/id/bill"
        page = pagetemplate.wrong_authentication_page(
            want_username = want_username,
            want_id_url = want_id,
            )
        page_data = page.serialise()
        self.failUnlessOutputCheckerMatch(
            "...%(want_id)s..." % vars(), page_data
            )


suite = scaffold.suite(__name__)

__main__ = scaffold.unittest_main

if __name__ == '__main__':
    import sys
    exitcode = __main__(sys.argv)
    sys.exit(exitcode)
