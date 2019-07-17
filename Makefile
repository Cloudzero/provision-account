# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

# Include Makefile Constants
include MakefileConstants.mk


####################
#
# Makefile Niceties
#
####################
# Add an implicit guard for parameter input validation; use as target dependency guard-VARIABLE_NAME, e.g. guard-AWS_ACCESS_KEY_ID
.PHONY: guard-%
guard-%:
	@if [ -z "${${*}}" ] ; then \
		printf \
			"$(ERROR_COLOR)ERROR:$(NO_COLOR) Variable [$(ERROR_COLOR)$*$(NO_COLOR)] not set.\n"; \
		exit 1; \
	fi


.PHONY: help                                                                            ## Prints the names and descriptions of available targets
help:
	@grep -E '^.PHONY: [a-zA-Z_%-\]+.*? ## .*$$' $(MAKEFILE_LIST) $${source_makefile} | cut -c 18- | sort | awk 'BEGIN {FS = "[ \t]+?## "}; {printf "\033[36m%-50s\033[0m %s\n", $$1, $$2}'


#################
#
# Dev Targets
#
#################
.PHONY: init                                                                            ## Install package dependencies for python
init: guard-VIRTUAL_ENV $(PYTHON_DEPENDENCY_FILE)
$(PYTHON_DEPENDENCY_FILE): $(REQUIREMENTS_FILES)
	for f in $^ ; do \
    pip install -r $${f} ; \
  done
	touch $(PYTHON_DEPENDENCY_FILE)


.PHONY: lint                                                                            ## Lints the code for all available runtimes
lint: lint-templates lint-sam-apps


.PHONY: lint-templates
lint-templates: $(CFN_LINT_OUTPUT)
$(CFN_LINT_OUTPUT): $(CFN_TEMPLATES)
	for t in $(CFN_TEMPLATES) ; do \
		cfn-lint -t $${t} ; \
	done

.PHONY: test                                                                            ## Lints then tests code for all available runtimes
test: lint test-sam-apps

# Generic Sam Apps Target, loop through SAM_APPS calling make with stem
.PHONY: %-sam-apps
%-sam-apps:
	for app in $(SAM_APPS) ; do \
    cd $${app} && $(MAKE) $* ; \
  done

.PHONY: clean                                                                           ## Cleans up everything that isn't source code (similar to re-cloning the repo)
clean: clean-sam-apps
	-rm -f $(PACKAGED_TEMPLATE_FILE)
	-touch $(REQUIREMENTS_FILES)
	-rm $(PYTHON_DEPENDENCY_FILE)
	-rm $(CFN_LINT_OUTPUT)
	-pip freeze | xargs pip uninstall -y -q


###################
#
# Deployment
#
###################

cfn-deploy: guard-stack_name guard-template_file
	@aws cloudformation deploy \
		--template-file $${template_file} \
		--stack-name $${stack_name} \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			BucketName=$(BUCKET) \
		--tags "cz:feature=$(FEATURE_NAME)" "cz:team=$(TEAM_NAME)"


cfn-delete: guard-stack_name
	@aws cloudformation delete-stack \
		--stack-name $${stack_name}
	@printf "Deleting stack $${stack_name} "
	@while aws cloudformation describe-stacks --stack-name $${stack_name} 2>/dev/null | grep -q IN_PROGRESS ; do \
		printf "." ; \
		sleep 1 ; \
	done ; \
	echo
	@aws cloudformation list-stacks | \
		jq -re --arg stackName $${stack_name} \
			'.StackSummaries | map(select(.StackName == $$stackName)) | .[0] | [.StackStatus, .StackStatusReason] | join(" ")'


cfn-describe: guard-stack_name
	@aws cloudformation describe-stacks \
		--stack-name $${stack_name}


cfn-dryrun: guard-stack_name guard-template_file
	@aws cloudformation deploy \
		--template-file $${template_file} \
		--stack-name $${stack_name} \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
		--no-fail-on-empty-changeset \
		--no-execute-changeset \
		--parameter-overrides \
			BucketName=$(BUCKET) \
		--tags "cz:feature=$(FEATURE_NAME)" "cz:team=$(TEAM_NAME)"



$(PACKAGED_TEMPLATE_FILE): $(TEMPLATE_FILE)
	account_id=`aws sts get-caller-identity | jq -r -e '.Account'` && \
	aws cloudformation package \
		--template-file $< \
		--output-template-file $@ \
		--s3-bucket cz-sam-deployment-$${account_id}


.PHONY: deploy-dry-run                                                                  ## Almost-deploys SAM template to AWS stack =)
deploy-dry-run: $(VIRTUAL_ENV) $(PACKAGED_TEMPLATE_FILE)
	@$(MAKE) cfn-dryrun stack_name=cz-$(FEATURE_NAME) template_file=$(PACKAGED_TEMPLATE_FILE)


.PHONY: deploy                                                                          ## Deploys Artifacts to S3 Bucket
deploy:
	@. ./project.sh && cz_assert_profile && \
	$(MAKE) $(PACKAGED_TEMPLATE_FILE) && \
	$(MAKE) package-sam-apps && \
	$(MAKE) cfn-deploy stack_name=cz-$(FEATURE_NAME) template_file=$(PACKAGED_TEMPLATE_FILE)
	version=`git rev-list --count HEAD` && \
	for cfn in $(CFN_TEMPLATES) ; do \
		aws s3 cp $${cfn} s3://$(BUCKET)/v$(SEMVER_MAJ_MIN).$${version}/$${cfn} && \
		aws s3 cp $${cfn} s3://$(BUCKET)/latest/$${cfn} ; \
	done && \
	for app in $(SAM_APPS) ; do \
		aws s3 cp $${app}/$(PACKAGED_TEMPLATE_FILE) s3://$(BUCKET)/v$(SEMVER_MAJ_MIN).$${version}/$${app}.yaml && \
		aws s3 cp $${app}/$(PACKAGED_TEMPLATE_FILE) s3://$(BUCKET)/latest/$${app}.yaml ; \
	done


.PHONY: describe                                                                        ## Return information about SAM-created stack from AWS
describe: $(VIRTUAL_ENV)
	@$(MAKE) cfn-describe stack_name=cz-$(FEATURE_NAME)


.PHONY: delete                                                                          ## Removes SAM-created stack from AWS
delete: $(VIRTUAL_ENV)
	@$(MAKE) cfn-delete stack_name=cz-$(FEATURE_NAME)
