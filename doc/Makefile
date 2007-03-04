#! /usr/bin/make -f

# Makefile
# Part of Gracie, an OpenID provider
#
# Copyright © 2007 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile for documentation

RST_SUFFIX = .txt

XHTML_SUFFIX = .html

RM = rm

RST2HTML = rst2html
RST2HTML_OPTS =


.PHONY: all
all:

.PHONY: doc
doc:

%${XHTML_SUFFIX}: %${RST_SUFFIX}
	$(RST2HTML) ${RST2HTML_OPTS} "$<" > "$@"

.PHONY: clean
clean:
