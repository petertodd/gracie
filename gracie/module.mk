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

version_info_module = ${MODULE_DIR}/version/version_info.py

VCS_VERSION_INFO ?= bzr version-info --format=python


${version_info_module}:
	$(VCS_VERSION_INFO) > $@


setuptools-build: ${version_info_module}
setuptools-install: ${version_info_module}
setuptools-clean: ${version_info_module}
