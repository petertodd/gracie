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
CODE_PACKAGE_DIRS := gracie
CODE_PROGRAM_DIR := bin
DOC_DIR := doc
TEST_DIR := test

# Variables that will be extended by module include files
GENERATED_FILES :=
CODE_MODULES :=
CODE_PROGRAMS :=

# List of modules (directories) that comprise our 'make' project
MODULES := ${CODE_PACKAGE_DIRS}
MODULES += ${CODE_PROGRAM_DIR}
MODULES += ${DOC_DIR}
MODULES += ${TEST_DIR}

RM = rm
MAKE_DIST_TARBALL=${CODE_PROGRAM_DIR}/make-dist-tarball


# Establish default goal
.PHONY: all
all:

# Include the make data for each module
include $(patsubst %,%/module.mk,${MODULES})


all: build

.PHONY: build
build:

.PHONY: dist
dist:
	$(MAKE_DIST_TARBALL)

.PHONY: install
install: build


include setuptools.mk

build: setuptools-build

.PHONY: bdist
bdist: setuptools-bdist

.PHONY: sdist
sdist: setuptools-sdist


.PHONY: clean
clean:
	$(RM) -rf ${GENERATED_FILES}
	find $(CURDIR) -name '*.pyc' -exec $(RM) {} +

clean: setuptools-clean


.PHONY: test
test:

.PHONY: qa
qa:

qa: setuptools-test


# Local Variables:
# mode: makefile
# coding: utf-8
# End:
# vim: filetype=make fileencoding=utf-8 :
