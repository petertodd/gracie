# doc/module.mk
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile module for documentation

MODULE_DIR := doc

DOC_NAMES = README TODO HACKING

RST_SUFFIX = .txt

XHTML_SUFFIX = .html
xhtml_doc_files = $(patsubst %,${MODULE_DIR}/%${XHTML_SUFFIX},${DOC_NAMES})

SVG_SUFFIX = .svg
svg_files = $(wildcard ${MODULE_DIR}/*${SVG_SUFFIX})

PNG_SUFFIX = .png
png_files = $(patsubst %${SVG_SUFFIX},%${PNG_SUFFIX},${svg_files})

LOGO_SIZES = 16 32 48 60 80 120
LOGO_NAME = gracie-logo
logo_files = $(patsubst %,${MODULE_DIR}/${LOGO_NAME}.%${PNG_SUFFIX},${LOGO_SIZES})

MANPAGES = gracied.8
manpage_files = $(patsubst %,${MODULE_DIR}/%,${MANPAGES})

GENERATED_FILES += ${xhtml_doc_files}
GENERATED_FILES += ${png_files}
GENERATED_FILES += ${logo_files}
GENERATED_FILES += ${manpage_files}

RST2HTML = rst2html
RST2HTML_OPTS =

CONVERT = convert


.PHONY: doc
doc: man xhtml images

build: doc


.PHONY: man
man: ${manpage_files}

%.1: %.1.sgml
	docbook-to-man $< > $@

%.8: %.8.sgml
	docbook-to-man $< > $@


.PHONY: xhtml
xhtml: ${xhtml_doc_files}

%${XHTML_SUFFIX}: %${RST_SUFFIX}
	$(RST2HTML) ${RST2HTML_OPTS} "$<" > "$@"


.PHONY: images
images: png logo

.PHONY: png
png: ${png_files}

.PHONY: logo
logo: ${logo_files}

%${PNG_SUFFIX}: %${SVG_SUFFIX}
	$(CONVERT) "$<" "$@"

%.16${PNG_SUFFIX}: %${SVG_SUFFIX}
	$(CONVERT) "$<" -geometry 16x16 "$@"

%.32${PNG_SUFFIX}: %${SVG_SUFFIX}
	$(CONVERT) "$<" -geometry 32x32 "$@"

%.48${PNG_SUFFIX}: %${SVG_SUFFIX}
	$(CONVERT) "$<" -geometry 48x48 "$@"

%.60${PNG_SUFFIX}: %${SVG_SUFFIX}
	$(CONVERT) "$<" -geometry 60x60 "$@"

%.80${PNG_SUFFIX}: %${SVG_SUFFIX}
	$(CONVERT) "$<" -geometry 80x80 "$@"

%.120${PNG_SUFFIX}: %${SVG_SUFFIX}
	$(CONVERT) "$<" -geometry 120x120 "$@"


# Local Variables:
# mode: makefile
# coding: utf-8
# End:
# vim: filetype=make fileencoding=utf-8 :
