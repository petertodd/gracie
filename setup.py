#! /usr/bin/env python
# -*- coding: utf-8 -*-

# setup.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Package setup script
"""

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name = "gracie",
    version = "0.1",
    packages = find_packages(
        exclude = ['gracie/test'],
    ),

    # setuptools metadata
    zip_safe = True,
    test_suite = "gracie.test.suite.suite",
    install_requires = """
        python-openid >= 1.2
    """,

    # PyPI metadata
    author = "Ben Finney",
    author_email = "ben+python@benfinney.id.au",
    description = "Gracie - OpenID provider for local accounts",
    license = "GPL",
    keywords = "gracie openid identity authentication provider",
    ### url = "http://example.org/projects/gracie/",
    long_description = """
        Gracie is an OpenID server (a "provider" in OpenID terminology) that
        serves OpenID identities for the local system PAM accounts. It
        authenticates users with a username/password challenge.

        The OpenID protocol is documented at <URL:http://openid.net/>.
    """,
    classifiers = [
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: System",
        "Operating System :: POSIX",
        "Intended Audience :: System Administrators",
    ],
)

