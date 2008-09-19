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

import os
import textwrap
import subprocess
import tempfile

import ez_setup
ez_setup.use_setuptools()

from setuptools import (
    setup,
    find_packages,
    )


version_info_module_file_name = "gracie/version/version_info.py"

def update_version_info_module():
    """ Update the version-info module file from VCS """

    def get_module_content(module_file_name):
        """ Return the content of the current module file """
        module_content = None
        try:
            module_file = open(module_file_name, 'r')
            module_content = module_file.read()
        except IOError:
            pass

        return module_content

    def get_updated_content():
        """ Return updated content (or None) for version-info module """
        content = None
        
        bzr_version_info_commandline = [
            "bzr", "version-info", "--format=python"
            ]
        module_file = tempfile.NamedTemporaryFile('w+')
        try:
            exit_status = subprocess.Popen(
                bzr_version_info_commandline,
                stdout=module_file,
                ).wait()
            if exit_status:
                raise OSError(
                    "Command failed: %(bzr_version_info_commandline)r" % vars())
            module_file.seek(0)
            content = module_file.read()
        except OSError:
            pass
        finally:
            module_file.close()

        return content

    update_required = False
    module_content = get_module_content(version_info_module_file_name)
    updated_module_content = get_updated_content()
    if updated_module_content is not None:
        if module_content is None:
            update_required = True
        else:
            if module_content != updated_module_content:
                update_required = True

    if update_required:
        module_file = open(version_info_module_file_name, 'w')
        module_file.write(updated_module_content)
        module_file.close()

update_version_info_module()


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
