# -*- coding: utf-8 -*-

# page.py
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
