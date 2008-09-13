#! /usr/bin/env python
# -*- coding: utf-8 -*-

# setup.py
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

""" Package setup script
"""

import textwrap

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

main_module_name = 'gracie'
main_module = __import__(main_module_name, fromlist=['version'])
version = main_module.version

short_description, long_description = (
    textwrap.dedent(d).strip()
    for d in main_module.__doc__.split('\n\n', 1)
    )


setup(
    name = main_module_name,
    version = version.version,
    packages = find_packages(
        exclude = ['test'],
        ),
    scripts = [
        "bin/gracied",
        ],

    # setuptools metadata
    zip_safe = False,
    test_suite = "test.suite.suite",
    install_requires = [
        "python-openid >= 1.2",
        "Routes >= 1.6.3",
        ],

    # PyPI metadata
    author = version.author_name,
    author_email = version.author_email,
    description = short_description,
    license = version.license,
    keywords = "gracie openid identity authentication provider",
    url = main_module._url,
    long_description = long_description,
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
