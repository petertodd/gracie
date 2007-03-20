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
SBIN_DEST = ${PREFIX}/sbin

SRC_DIR = src
DOC_DIR = doc
BIN_DIR = bin
SBIN_DIR = sbin

BIN_FILES =
SBIN_FILES = \
	${SBIN_DIR}/gracied

PROJECT_DIRS = ${SRC_DIR} ${DOC_DIR}

RM = rm
PYTHON = python
EASY_INSTALL = easy_install


.PHONY: all
all: build

.PHONY: doc
doc:
	$(MAKE) --directory=${DOC_DIR} "$@"

.PHONY: build
build: build-stamp
build-stamp:
	$(MAKE) --directory=${SRC_DIR} "$@"
	touch "$@"

.PHONY: install
install: build
	install -d ${BIN_DEST} ${SBIN_DEST}
	### install -m 755 -t ${BIN_DEST} ${BIN_FILES}
	install -m 755 -t ${SBIN_DEST} ${SBIN_FILES}
	echo Install the Python egg using easy_install.

.PHONY: test
test:
	$(MAKE) --directory=${SRC_DIR} "$@"

.PHONY: clean
clean:
	- $(RM) *-stamp
	- $(RM) *.egg
	for dir in ${PROJECT_DIRS} ; do \
		$(MAKE) --directory=$${dir} "$@" ; \
	done
