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

import os
import stat

from setuptools import setup, find_packages
from setuptools.command.install_scripts import install_scripts

main_module_name = 'gracie'
main_module = __import__(main_module_name)

description = main_module.__doc__.split('\n\n', 1)


class gracie_install_scripts(install_scripts):
    """ Custom install_scripts command for Gracie """

    def run(self):
        """ Run the command """
        self.mkpath(os.path.normpath(self.install_dir))

        self.outfiles = []
        _p = os.path.join
        scripts = {
            _p(self.build_dir, "bin/gracied"): self.install_dir,
        }
        for src_file, dest_dir in scripts.items():
            ofile, copied = self.copy_file(src_file, dest_dir)
            if copied:
                self.outfiles.append(ofile)

        if os.name == "posix":
            for ofile in self.get_outputs():
                if not self.dry_run:
                    mode = os.stat(ofile)[stat.ST_MODE]
                    new_mode = (mode | 0555) & 07777
                    os.chmod(ofile, new_mode)


setup(
    name = main_module_name,
    version = main_module.__version__,
    packages = find_packages(
        exclude = ['test'],
    ),
    cmdclass = {
        'install_scripts': gracie_install_scripts,
    },

    # setuptools metadata
    zip_safe = True,
    test_suite = "test.suite.suite",
    install_requires = [
        "python-openid >= 1.2",
        "Routes >= 1.6.3",
    ],

    # PyPI metadata
    author = main_module.__author_name__,
    author_email = main_module.__author_email__,
    description = description[0].strip(),
    license = main_module.__license__,
    keywords = "gracie openid identity authentication provider",
    url = main_module.__url__,
    long_description = description[1],
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

