#! /usr/bin/make -f

# Makefile
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile for Gracie project

PROJECT_MODS = gracie
DOC_DIR = doc
PROJECT_DIRS = ${DOC_DIR} ${PROJECT_MODS}

DOC_SRC_SUFFIX = .txt
DOC_NAMES = README
doc_src = $(addsuffix ${DOC_SRC_SUFFIX},${DOC_NAMES})

XHTML_SUFFIX = .html
xhtml_files = $(addsuffix ${XHTML_SUFFIX},${DOC_NAMES})

RM = rm

PYTHON = python

RST2HTML = rst2html
RST2HTML_OPTS =


.PHONY: all
all:

.PHONY: doc
doc: xhtml
	$(MAKE) --directory=${DOC_DIR}

xhtml: ${xhtml_files}
${xhtml_files}: ${doc_src_files}

%${XHTML_SUFFIX}: %${DOC_SRC_SUFFIX}
	$(RST2HTML) ${RST2HTML_OPTS} "$<" > "$@"

.PHONY: test
test:
	@ for dir in ${PROJECT_MODS} ; do \
		$(MAKE) --directory=$${dir} "$@" ; \
	done

.PHONY: clean
clean:
	$(RM) -f ${xhtml_files}
	for dir in ${PROJECT_DIRS} ; do \
		$(MAKE) --directory=$${dir} "$@" ; \
	done
