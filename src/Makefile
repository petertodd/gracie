#! /usr/bin/make -f

# Makefile
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile for gracie module

PREFIX ?= /usr
BIN_DEST = ../bin
SBIN_DEST = ../sbin
EGG_DEST = ..

BIN_FILES =
SBIN_FILES = gracied

SETUP_SCRIPT = ./setup.py
SETUP_PY24 = python2.4 ${SETUP_SCRIPT}
SETUP_PY25 = python2.5 ${SETUP_SCRIPT}
SETUP = $(PYTHON) ${SETUP_SCRIPT}

BDIST_TARGETS = bdist_egg
SETUP_TARGETS = test register sign install

RM = rm
PYTHON = python

VCS_INVENTORY = bzr inventory


.PHONY: all
all: build

.PHONY: build
build: build-stamp
build-stamp:
	install -d ${BIN_DEST} ${SBIN_DEST}
	### install -m 755 -t ${BIN_DEST} ${BIN_FILES}
	install -m 755 -t ${SBIN_DEST} ${SBIN_FILES}
	$(SETUP) bdist_egg
	cp dist/*.egg ${EGG_DEST}/.
	touch "$@"

.PHONY: install
install:
	$(SETUP) install --prefix=${PREFIX}

.PHONY: test
test:
	@ $(PYTHON) ./test/suite.py

.PHONY: clean
clean:
	- $(RM) *-stamp
	- $(RM) -rf ${BIN_DEST} ${SBIN_DEST}
	- $(RM) MANIFEST MANIFEST.in
	- $(RM) -rf *.egg-info/
	- $(RM) -rf build/ dist/

.PHONY: dist
dist: sdist bdist upload

.PHONY: upload
upload: upload-stamp
upload-stamp: test register
	$(SETUP) sdist upload
	$(SETUP_PY24) ${BDIST_TARGETS} upload
	touch $@

.PHONY: register
register: register-stamp
register-stamp:
	$(SETUP) register
	touch $@

.PHONY: bdist
bdist: bdist-stamp
bdist-stamp: ${BDIST_TARGETS}
	touch $@

.PHONY: ${BDIST_TARGETS}
${BDIST_TARGETS}:
	$(SETUP_PY24) $@

.PHONY: sdist
sdist: sdist-stamp
sdist-stamp: MANIFEST.in
	$(SETUP) sdist
	touch $@

MANIFEST.in:
	( \
		$(VCS_INVENTORY) \
		| sed -e 's/^/include /' \
	) > $@

