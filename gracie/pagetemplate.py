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

</head>
$page_body
</html>
""")

body_template = Template("""\
<body>
<div id="content">
$auth_section
<h1 id="title">$page_title</h1>
$page_content
</div><!-- content -->
</body>
""")

auth_section_template = Template("""\
<div id="auth-info">
<p>$logged_in_as
$change_status
</p>
</div><!-- auth-info -->
""")

openid_url_prefix = "http://localhost:8000/id/"


class Page(object):
    """ Web page """

    def __init__(self, title=None):
        """ Set up a new instance """
        self.character_encoding = "utf-8"
        self.title = title
        self.content = ""
        self.values = dict(
            auth_entry = None,
            login_url = None,
            logout_url = None,
        )

    def _get_auth_section(self, auth_entry):
        """ Get the authentication info section """
        login_url = self.values['login_url']
        logout_url = self.values['logout_url']
        logged_in_as = "You are not logged in."
        change_status = (
            """You may <a href="%(login_url)s">log in now</a>."""
            % locals()
        )
        if auth_entry:
            fullname = auth_entry['fullname']
            openid_url = self.values['openid_url']
            login_url = self.values['login_url']
            logged_in_as = ("""\
                Logged in as <a href="%(openid_url)s">%(openid_url)s</a>
                (%(fullname)s)
                """ % locals()
            )
            change_status = (
                """You may <a href="%(logout_url)s">log out now</a>."""
                % locals()
            )
        auth_section_text = auth_section_template.substitute(locals())
        return auth_section_text

    def serialise(self):
        """ Generate a text stream for page data """
        auth_section_text = self._get_auth_section(
            self.values['auth_entry'])
        content_text = Template(self.content).substitute(self.values)
        body_text = body_template.substitute(self.values,
            page_title=self.title,
            auth_section=auth_section_text,
            page_content=content_text,
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

def about_site_view_page():
    title = "About this site"
    page = Page(title)
    page.content = """
        This is Gracie, an OpenID provider.
    """
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
        <input type="submit" name="submit" value="Sign in" />
        <input type="submit" name="cancel" value="Cancel" />
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

def login_cancelled_page():
    title = "Login Cancelled"
    page = Page(title)
    page.content = """
        The login was cancelled.
        You can <a href="/login">log in now</a> if you want.
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

def login_auth_succeeded_page(name):
    title = "Login Succeeded"
    page = Page(title)
    page.values.update(dict(name=name))
    page.content = """
        You can <a href="/id/$name">view your identity page</a>.
    """
    return page
