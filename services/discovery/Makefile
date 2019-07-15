# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

####################
#
# Project Constants
#
####################
FEATURE = provision-account-discovery
SRC_FILES = $(shell find src -name "*.py")
TEST_FILES = $(shell find tests -name "test_*.py")
PYTHON_DEPENDENCY_FILE = .cz_py_dependencies_installed
REQUIREMENTS_FILES = $(shell find . -name "requirements*.txt")
COVERAGE_REPORT = coverage-report
FLAKE8_OUT = flake8.out
TEMPLATE = template.yaml
PACKAGED_TEMPLATE = packaged.template.yaml
BUILD_DIR = .aws-sam
DEPLOYMENT_FILE = .deploy


####################
#
# Makefile Niceties
#
####################
.PHONY: guard-%
guard-%:
	@if [ -z "${${*}}" ] ; then \
		printf \
			"$(ERROR_COLOR)ERROR:$(NO_COLOR) Variable [$(ERROR_COLOR)$*$(NO_COLOR)] not set.\n"; \
		exit 1; \
	fi

.PHONY: help                                          ## Prints the names and descriptions of available targets
help:
	@grep -E '^.PHONY: [a-zA-Z_%-\]+.*? ## .*$$' $(MAKEFILE_LIST) | cut -c 9- | sort | awk 'BEGIN {FS = "[ \t]+?## "}; {printf "\033[36m%-50s\033[0m %s\n", $$1, $$2}'

.PHONY: clean                                         ## Clean python c files, reports, and build dir
clean:
	-rm $(FLAKE8_OUT)
	-rm -rf $(COVERAGE_REPORT)
	-rm -rf $(BUILD_DIR)
	-touch $(PYTHON_DEPENDENCY_FILE)
	-find . -name '*.pyc' -exec rm -f {} +
	-find . -name '*.pyo' -exec rm -f {} +
	-find . -name '*~' -exec rm -f {} +
	-find . -name '__pycache__' -exec rm -fr {} +


#################
#
# Dev Targets
#
#################
.PHONY: init                                          ## Initialize Python Environment. Requires $(VIRTUAL_ENV)
init: guard-VIRTUAL_ENV $(PYTHON_DEPENDENCY_FILE)
$(PYTHON_DEPENDENCY_FILE): $(REQUIREMENTS_FILES)
	for f in $^ ; do \
    pip install -r $${f} ; \
  done
	touch $(PYTHON_DEPENDENCY_FILE)


.PHONY: lint                                          ## Lint Python Files via Flake8
lint: $(FLAKE8_OUT)
$(FLAKE8_OUT): $(SRC_FILES) $(TEST_FILES) tox.ini
	@flake8 --output-file=$(FLAKE8_OUT)


.PHONY: test                                          ## Run Tests and Produce Coverage Report
test: init lint $(COVERAGE_REPORT)
$(COVERAGE_REPORT): $(SRC_FILES) $(TEST_FILES)
	@pytest src tests \
		--doctest-modules \
		--cov src \
		--cov-report html:$(COVERAGE_REPORT) \
		--cov-branch \
		-vvv

.PHONY: build                                         ## Build sam app
build: $(BUILD_DIR)
$(BUILD_DIR): $(SRC_FILES) $(TEMPLATE)
	sam build

.PHONY: package
package: $(PACKAGED_TEMPLATE)
$(PACKAGED_TEMPLATE): $(BUILD_DIR)
	account_id=`aws sts get-caller-identity | jq -r -e '.Account'` && \
	sam package \
		--s3-bucket $${BUCKET:=cz-sam-deployment-$${account_id}} \
		--output-template-file $@


.PHONY: deploy
deploy: $(DEPLOYMENT_FILE)
$(DEPLOYMENT_FILE): $(PACKAGED_TEMPLATE)
	sam deploy \
		--template-file $^ \
		--stack-name cz-$${namespace:-${NAMESPACE}}-$(FEATURE) \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM


####################
#
# Util Constants
#
####################
ERROR_COLOR = \033[1;31m
INFO_COLOR = \033[1;32m
WARN_COLOR = \033[1;33m
NO_COLOR = \033[0m
