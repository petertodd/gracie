# test/module.mk
# Part of Gracie, an OpenID provider
#
# Copyright © 2007-2008 Ben Finney <ben+python@benfinney.id.au>
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later.
# No warranty expressed or implied. See the file LICENSE for details.

# Makefile module for test suite

MODULE_DIR := test

TEST_SUITE = ${TEST_DIR}/suite.py

GENERATED_FILES += .coverage

PYFLAKES = pyflakes
PYLINT = pylint
COVERAGE = python-coverage
DATE = date
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

INWAIT = inotifywait
inwait_events_opts =
inwait_events_opts += -e create
inwait_events_opts += -e modify
inwait_events_opts += -e delete
inwait_exclude_regex = '(\#.+\#|\..+\.sw[[:alpha:]])$$'
INWAIT_OPTS = -r -t 0 ${inwait_events_opts} --exclude ${inwait_exclude_regex}
TEST_INWAIT_FILES = ${CODE_PACKAGE_DIRS} ${CODE_PROGRAMS} ${TEST_DIR}


# usage: $(call test-output-banner,message)
define test-output-banner
	@ echo -n ${1} ; \
	$(DATE) +${DATE_FORMAT}
endef


test:
	$(call test-output-banner, "Test run: " )
	$(PYTHON) ${TEST_SUITE}

# usage: $(call test-wait)
define test-wait
	$(INWAIT) ${INWAIT_OPTS} ${TEST_INWAIT_FILES}
endef

.PHONY: test-continuous
test-continuous:
	while true ; do \
		clear ; \
		$(MAKE) test ; \
		$(call test-wait) ; \
	done


.PHONY: pyflakes
pyflakes:
	$(PYFLAKES) .

.PHONY: pylint
pylint:
	$(PYLINT) ${CODE_PACKAGE_DIRS}
	$(PYLINT) ${CODE_PROGRAMS}
	$(PYLINT) ${TEST_DIR}

.PHONY: coverage
coverage:
	$(COVERAGE) -x ${TEST_SUITE}
	$(COVERAGE) -r -m ${CODE_MODULES} ${CODE_PROGRAMS}

qa: pyflakes coverage


# Local Variables:
# mode: makefile
# coding: utf-8
# End:
# vim: filetype=make fileencoding=utf-8 :
