# :vim: filetype=make : -*- makefile; coding: utf-8; -*-

# gracie/module.mk
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile module for gracie Python package

MODULE_DIR := gracie

CODE_MODULES += $(shell find ${MODULE_DIR} -name '*.py')

version_info_module := ${MODULE_DIR}/version/version_info.py

VCS_VERSION_INFO_PYTHON ?= bzr version-info --format=python


.PHONY: version-info
version-info:
	$(VCS_VERSION_INFO_PYTHON) > ${version_info_module}


setuptools-build: version-info
setuptools-install: version-info
setuptools-clean: version-info
setuptools-sdist: version-info
setuptools-bdist: version-info
