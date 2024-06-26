# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

# Include Makefile Constants
include ../../MakefileConstants.mk

####################
#
# Project Constants
#
####################
APP_NAME = $(FEATURE_NAME)-discovery
SRC_FILES = $(shell find src -name "*.py")
TEST_FILES = $(shell find tests -name "test_*.py")
COVERAGE_REPORT = coverage-reports
COVERAGE_XML = coverage.xml
BUILD_DIR = .aws-sam
TEMP_DIR = temp
DEPLOYMENT_FILE = .deploy
ACCOUNT_ID = $(shell source ../../project.sh && cz_assert_profile &> /dev/null && \
							 aws sts get-caller-identity | jq -r -e '.Account')


####################
#
# Guard Defaults
#
####################
bucket = $${BUCKET:=cz-sam-deployment-$(ACCOUNT_ID)}  # DEFAULT deployment bucket
namespace = $${namespace:-${NAMESPACE}}  # DEFAULT namespace


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


.PHONY: default-%
default-%:
	@printf "$(WARN_COLOR)$*$(NO_COLOR): $(INFO_COLOR)$($*)$(NO_COLOR)\n"


.PHONY: defaults                                      ## Prints the names and values of defaults
defaults:
	@grep -E '^[a-z]+\ =.*DEFAULT' $(MAKEFILE_LIST) | cut -c 10- | cut -f1 -d= | sort | \
		while read var ; do $(MAKE) default-$${var} ; done

.PHONY: clean                                         ## Clean python c files, reports, and build dir
clean:
	-rm $(APP_ZIP)
	-rm $(LINT_RESULTS)
	-rm -rf $(COVERAGE_REPORT) $(COVERAGE_XML)
	-rm -rf $(BUILD_DIR)
	-find . -name '*.pyc' -exec rm -f {} +
	-find . -name '*.pyo' -exec rm -f {} +
	-find . -name '*~' -exec rm -f {} +
	-find . -name '__pycache__' -exec rm -fr {} +
	-find . -name '*.pytest_cache' -exec rm -fr {} +
	-find . -name '*.coverage' -exec rm -fr {} +
	-find . -name 'temp' -exec rm -fr {} +


#################
#
# Dev Targets
#
#################
.PHONY: lint                                          ## Lint Python Files via Flake8
lint:
	@flake8 --output-file=$(LINT_RESULTS)


.PHONY: test                                          ## Run Tests and Produce Coverage Report
test:
	@pytest src tests


#################
#
# Convenience SAM wrapper targets for development.
# All official deployment automation is done in the root Makefile.
#
#################
.PHONY: build-python
build-python:
	mkdir -p $(TEMP_DIR)
	cp -r src $(TEMP_DIR)/src
	pip install -r requirements.txt -t $(TEMP_DIR)

.PHONY: build                                         ## Build sam app
build: $(BUILD_DIR) 
$(BUILD_DIR): $(SRC_FILES) $(TEMPLATE_FILE) build-python
	sam build

.PHONY: package
package: $(APP_ZIP)
$(APP_ZIP): $(BUILD_DIR)
	rm -f $@ ; cd $(TEMP_DIR) ; zip -rq ./../$@ .


.PHONY: deploy
deploy: $(DEPLOYMENT_FILE)
$(DEPLOYMENT_FILE): $(PACKAGED_TEMPLATE_FILE) guard-namespace
	@$(MAKE) defaults
	@. ../../project.sh && cz_assert_profile && \
  sam deploy \
		--template-file $< \
		--stack-name "cz-$(namespace)-$(APP_NAME)" \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
