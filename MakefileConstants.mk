# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

# Main parameters
FEATURE_NAME ?= provision-account
TEAM_NAME ?= cloudzero
BUCKET := cz-$(FEATURE_NAME)
SEMVER_MAJ_MIN := 1.0

# Util constants
ERROR_COLOR := \033[1;31m
INFO_COLOR := \033[1;32m
WARN_COLOR := \033[1;33m
NO_COLOR := \033[0m

# Prerequisite verification
REQUIREMENTS_FILES := $(shell find . -name "requirements*.txt")
PYTHON_DEPENDENCY_FILE := .cz_py_dependencies_installed

# Testing
CFN_LINT_OUTPUT := cfn-lint.output

# CFN Constants
TEMPLATE_FILE := template.yaml
PACKAGED_TEMPLATE_FILE := packaged-template.yaml
