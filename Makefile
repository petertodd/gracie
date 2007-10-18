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

PYVERS = 2.4 2.5
PYTHON = python
SETUP_SCRIPT = ./setup.py
SETUP = $(PYTHON) ${SETUP_SCRIPT}

BDIST_TARGETS = bdist_egg
SETUP_TARGETS = test register sign install

TEST_SUITE = ./test/suite.py
CODE_MODULES = ./gracie/*.py ./bin/gracied

RM = rm
PYFLAKES = pyflakes
### COVERAGE = python-coverage
COVERAGE = ./test/coverage.py

VCS_INVENTORY = bzr inventory


.PHONY: all
all: build

.PHONY: doc
doc:
	$(MAKE) --directory=${DOC_DIR} $@

.PHONY: build
build: build-stamp
build-stamp: ${PYVERS:%=build-python%-stamp}
	touch $@

build-python%-stamp:
	python$* ${SETUP_SCRIPT} build
	touch $@

.PHONY: install
install: install-stamp
install-stamp: ${PYVERS:%=install-python%-stamp}
	touch $@

install-python%-stamp:
	python$* ${SETUP_SCRIPT} install --prefix=${PREFIX}
	touch $@

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
upload: sdist-upload bdist-upload

.PHONY: register
register: register-stamp
register-stamp:
	$(SETUP) register
	touch $@

.PHONY: bdist
bdist: test ${PYVERS:%=bdist-python%-stamp}

bdist-python%-stamp:
	python$* ${SETUP_SCRIPT} ${BDIST_TARGETS}
	touch $@

.PHONY: bdist-upload
bdist-upload: test register ${PYVERS:%=bdist-python%-upload-stamp}

bdist-python%-upload-stamp:
	python$* ${SETUP_SCRIPT} ${BDIST_TARGETS} upload
	touch $@

.PHONY: sdist
sdist: sdist-stamp
sdist-stamp: MANIFEST.in
	$(SETUP) sdist
	touch $@

.PHONY: sdist-upload
sdist-upload: MANIFEST.in test register
	$(SETUP) sdist upload

MANIFEST.in:
	( \
		$(VCS_INVENTORY) \
		| sed -e 's/^/include /' \
	) > $@

