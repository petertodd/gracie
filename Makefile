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

# Include the make data for each module
include $(patsubst %,%/module.mk,${MODULES})


.PHONY: all
all: build

.PHONY: build
build:

.PHONY: install
install: build


include setuptools.mk

.PHONY: dist
dist: sdist bdist

.PHONY: bdist
bdist: setuptools-bdist

.PHONY: sdist
sdist: setuptools-sdist


.PHONY: clean
clean:
	$(RM) -rf ${GENERATED_FILES}


.PHONY: test
test:

.PHONY: qa
qa:
