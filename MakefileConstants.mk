# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

# Main parameters
FEATURE_NAME ?= provision-accounts
TEAM_NAME ?= cloudzero
SRC_FILES = $(shell find . -name "*.yaml")

# Util constants
ERROR_COLOR = \033[1;31m
INFO_COLOR = \033[1;32m
WARN_COLOR = \033[1;33m
NO_COLOR = \033[0m

# Prerequisite verification
REQUIREMENTS_FILE = requirements-dev.txt

# Git
# GIT_REV := $(shell git rev-parse HEAD)

# CFN Constants
TEMPLATE_FILE = template.yaml
PACKAGED_TEMPLATE_FILE = packaged-template.yaml
