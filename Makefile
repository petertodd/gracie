#! /usr/bin/make -f

# Makefile
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile for Gracie project

SHELL = /bin/bash
PATH = /usr/bin:/bin

# Directories with semantic meaning
PREFIX ?= /usr/local
CODE_PACKAGE_DIRS := gracie
DOC_DIR := doc
CODE_PROGRAM_DIR := bin
TEST_DIR := test

# Variables that will be extended by module include files
GENERATED_FILES :=
CODE_MODULES :=
CODE_PROGRAMS :=
DOCUMENT_TARGETS :=

# List of modules (directories) that comprise our 'make' project
MODULES := ${CODE_PACKAGE_DIRS}
MODULES += ${CODE_PROGRAM_DIR}
MODULES += ${DOC_DIR}
MODULES += ${TEST_DIR}



BIN_DEST = ${PREFIX}/bin

DOC_DIR = doc

PYVERS = 2.4 2.5
PYTHON = python
SETUP_SCRIPT = ./setup.py
SETUP = $(PYTHON) ${SETUP_SCRIPT}

BDIST_TARGETS = bdist_egg
SETUP_TARGETS = test register sign install

CODE_MODULES = ./gracie/*.py

GENERATED_FILES = *-stamp
GENERATED_FILES += ${BIN_DEST}
GENERATED_FILES += MANIFEST MANIFEST.in
GENERATED_FILES += *.egg-info/
GENERATED_FILES += build/ dist/



RM = rm

# Include the make data for each module
include $(patsubst %,%/module.mk,${MODULES})


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

.PHONY: clean
clean:
	$(RM) -rf ${GENERATED_FILES}

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



.PHONY: test
test:

.PHONY: qa
qa:
