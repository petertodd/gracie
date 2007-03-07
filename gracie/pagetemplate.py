# -*- coding: utf-8 -*-

# pagetemplate.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Response page generation for OpenID provider
"""

from string import Template


page_template = Template("""\
<?xml version="1.0" encoding="$character_encoding" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" >
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/xhtml; $character_encoding" />

    <title>$page_title</title>

    <style type="text/css">

    </style>

    <!-- OpenID data -->
    <link rel="openid.server" href="http://videntity.org/server" />
    <link rel="openid.delegate" href="http://bignose.videntity.org/" />

</head>
$page_body
</html>
""")

body_template = Template("""\
<body>
<div id="content">
<h1 id="title">$page_title</h1>
$page_content
</div><!-- content -->
</body>
""")


class Page(object):
    """ Web page """

    def __init__(self, title=None):
        """ Set up a new instance """
        self.character_encoding = "utf-8"
        self.title = title
        self.content = ""
        self.values = dict()

    def serialise(self):
        """ Generate a text stream for page data """
        content_text = Template(self.content).substitute(self.values)
        body_text = body_template.substitute(
            page_title=self.title, page_content=content_text,
        )
        page_text = page_template.substitute(
            page_title=self.title, page_body=body_text,
            character_encoding=self.character_encoding,
        )
        return page_text


def url_not_found_page(url):
    title = "Resource Not Found"
    page = Page(title)
    page.content = """
        The requested resource was not found: $want_url
    """
    page.values.update(dict(
        want_url = url,
    ))
    return page

def user_not_found_page(name):
    title = "User Not Found"
    page = Page(title)
    page.content = """
        The requested user name does not exist: $user_name
    """
    page.values.update(dict(
        user_name = name,
    ))
    return page

def identity_user_not_found_page(name):
    page = user_not_found_page(name)
    return page

def identity_view_user_page(entry):
    title = "Identity page for %(name)s" % entry
    page = Page(title)
    page.content = """
        User ID: $id
        Name: $name
        Full name: $fullname
    """
    page.values.update(entry)
    return page

def login_user_not_found_page(name):
    page = user_not_found_page(name)
    return page

def _login_form(message="", name=""):
    form_text = """
        <p class="message">$message</p>
        <form id="login" action="/login" method="POST">
        <p>
        <label for="username">Username</label>
        <input name="username" type="text" value="$username" />
        </p>
        <p>
        <label for="password">Password</label>
        <input name="password" type="password" />
        </p>
        <p>
        <input type="submit" value="Sign in" />
        </p>
        </form>
    """
    values = dict(message=message, username=name)
    form_text = Template(form_text).substitute(values)
    return form_text

def login_view_page():
    title = "Login"
    form_text = _login_form()
    page = Page(title)
    page.values.update(dict(form=form_text))
    page.content = """
        $form
    """
    return page

def login_submit_failed_page(message, name):
    title = "Login Failed"
    form_text = _login_form(message, name)
    page = Page(title)
    page.values.update(dict(form=form_text))
    page.content = """
        $form
    """
    return page
