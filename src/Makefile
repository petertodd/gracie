#! /usr/bin/make -f

# Makefile
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile for gracie module

BIN_DEST = ../bin
SBIN_DEST = ../sbin
LIB_DEST = ../gracie

BIN_FILES =
SBIN_FILES = gracied
LIB_FILES = $(wildcard gracie/*.py)

RM = rm
PYTHON = python


.PHONY: all
all: build

.PHONY: build
build: build-stamp
build-stamp:
	install -d ${BIN_DEST} ${SBIN_DEST} ${LIB_DEST}
	### install -m 755 -t ${BIN_DEST} ${BIN_FILES}
	install -m 755 -t ${SBIN_DEST} ${SBIN_FILES}
	install -m 644 -t ${LIB_DEST} ${LIB_FILES}
	touch "$@"

.PHONY: test
test:
	@ $(PYTHON) ./test/suite.py

.PHONY: clean
clean:
	- $(RM) *-stamp
	- $(RM) -r ${BIN_DEST} ${SBIN_DEST} ${LIB_DEST}

