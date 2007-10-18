#! /usr/bin/make -f

# Makefile
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile for Gracie project

PREFIX ?= /usr/local

BIN_DEST = ${PREFIX}/bin

DOC_DIR = doc
BIN_DIR = bin

BIN_FILES = ${BIN_DIR}/gracied

SETUP_SCRIPT = ./setup.py
SETUP_PY24 = python2.4 ${SETUP_SCRIPT}
SETUP_PY25 = python2.5 ${SETUP_SCRIPT}
SETUP = $(PYTHON) ${SETUP_SCRIPT}

BDIST_TARGETS = bdist_egg
SETUP_TARGETS = test register sign install

TEST_SUITE = ./test/suite.py
CODE_MODULES = ./gracie/*.py ./bin/gracied

RM = rm
PYTHON = python
PYFLAKES = pyflakes
### COVERAGE = python-coverage
COVERAGE = ./test/coverage.py

VCS_INVENTORY = bzr inventory


.PHONY: all
all: build

.PHONY: doc
doc:
	$(MAKE) --directory=${DOC_DIR} "$@"

.PHONY: build
build: build-stamp
build-stamp:
	install -d ${BIN_DEST}
	install -m 755 -t ${BIN_DEST} ${BIN_FILES}
	$(SETUP_PY24) bdist_egg
	$(SETUP_PY25) bdist_egg
	cp dist/*.egg ${EGG_DEST}/.
	touch "$@"

.PHONY: install
install:
	$(SETUP) install --prefix=${PREFIX}

.PHONY: test
test:
	$(SETUP) test --quiet

.PHONY: flakes
flakes:
	$(PYFLAKES) .

.PHONY: coverage
coverage:
	$(COVERAGE) -x ${TEST_SUITE}
	$(COVERAGE) -r -m ${CODE_MODULES}

.PHONY: qa
qa: flakes coverage

.PHONY: clean
clean:
	- $(RM) *-stamp
	- $(RM) -rf ${BIN_DEST}
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
	$(SETUP_PY25) ${BDIST_TARGETS} upload
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
	$(SETUP_PY25) $@

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

