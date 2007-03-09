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
    $css_sheet
    </style>

</head>
$page_body
</html>
""")

body_template = Template("""\
<body>
$page_header
<div id="content">
<h1 id="title">$page_title</h1>
$page_content
</div><!-- content -->
$page_footer
</body>
""")

header_template = Template("""\
<div id="header">
<p id="banner"><a href="/">Gracie</a></p>
$auth_section
</div><!-- banner -->
""")

footer_template = Template("""\
<div id="footer">
</div><!-- footer -->
""")

auth_section_template = Template("""\
<div id="auth-info">
<p>$logged_in_as</p>
<p>$change_status</p>
</div><!-- auth-info -->
""")

css_sheet = """\
body {
    width: 100%;
    height: auto;
    margin: 0.0em;
    color: black;
    background-color: #FFB;
}

div#header {
    color: black;
    background-color: #FFC;
    height: 3.0em;
    margin: 0.0em;
    border: 0;
    border-bottom: 2px solid black;
    padding: 0.2em;
    padding-left: 1.0em;
}

div#footer {
    border: 0;
    border-top: 1px solid black;
}

p#banner {
    width: 60%;
    float: left;
}

div#auth-info {
    float: right;
    color: black;
    background-color: #BCF;
    margin: 0.0em;
    border: 1px solid #88A;
    padding: 0.3em 0.5em;
    width: 30%;
    font-family: sans-serif;
    font-size: 70%;
    text-align: right;
}

div#content {
    margin: 0.0em;
    padding: 0.5em;
}
"""

openid_url_prefix = "http://localhost:8000/id/"


class Page(object):
    """ Web page """

    def __init__(self, title=None):
        """ Set up a new instance """
        self.character_encoding = "utf-8"
        self.title = title
        self.css_sheet = css_sheet,
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
        text = auth_section_template.substitute(locals())
        return text

    def _get_header(self):
        """ Get the page header """
        auth_section_text = self._get_auth_section(
            self.values['auth_entry'])
        text = header_template.substitute(self.values,
            auth_section=auth_section_text,
        )
        return text

    def _get_footer(self):
        """ Get the page footer """
        text = footer_template.substitute(self.values,
        )
        return text

    def serialise(self):
        """ Generate a text stream for page data """
        header_text = self._get_header()
        content_text = Template(self.content).substitute(self.values)
        footer_text = self._get_footer()
        body_text = body_template.substitute(self.values,
            page_title=self.title,
            page_header=header_text, page_footer=footer_text,
            page_content=content_text,
        )
        page_text = page_template.substitute(
            page_title=self.title, page_body=body_text,
            css_sheet=self.css_sheet,
            character_encoding=self.character_encoding,
        )
        return page_text


def internal_error_page(message):
    title = "Internal Server Error"
    page = Page(title)
    page.content = """
        The server encountered an error trying to serve the request.
        The message was: $message
    """
    page.values.update(dict(
        message = message,
    ))
    return page

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
        <div id="identity-info">
        <table>
        <tr><th>User ID</th><td>$id</td></tr>
        <tr><th>Name</th><td>$name</td></tr>
        <tr><th>Full name</th><td>$fullname</td></tr>
        </table>
        </div><!-- identity-info -->
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
