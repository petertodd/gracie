# :vim: filetype=make : -*- makefile; coding: utf-8; -*-

# test/module.mk
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile module for test suite

MODULE_DIR := test

TEST_SUITE = ${TEST_DIR}/suite.py

GENERATED_FILES += .coverage

PYFLAKES = pyflakes
PYLINT = pylint
# TODO: Revert to Debian packaged version when it installs this version of the module
COVERAGE = $(PYTHON) ${TEST_DIR}/coverage.py


test:
	$(PYTHON) ${TEST_SUITE}

.PHONY: pyflakes
pyflakes:
	$(PYFLAKES) .

.PHONY: pylint
pylint:
	$(PYLINT) ${CODE_PACKAGE_DIRS}
	$(PYLINT) ${CODE_PROGRAMS}
	$(PYLINT) ${TEST_DIR}

.PHONY: coverage
coverage:
	$(COVERAGE) -x ${TEST_SUITE}
	$(COVERAGE) -r -m ${CODE_MODULES} ${CODE_PROGRAMS}

qa: pyflakes coverage
