# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

#!/usr/bin/env bash

# Useful macro functions for controlling AWS profiles/sessions and other useful environment vars.
# These functions can be sourced and used with make, but they can also be used with any other console
# tool that uses the standard AWS environment variables. Requires the AWS CLI to be installed and on the path.


get_role_session_name(){
  echo $(hostname | cut -f1 -d.)-cz-project-profile
}


# Assume a role that's named by a profile in ~/.aws/credentials.
# Persist this session using environment variables.
# Common pattern for developers, but can also be used with CI if the credentials file is set up ahead of time.
cz_use_profile() {
    local target_profile=${1?} ; shift
    local mfa_code=${1}

    cz_clear_profile

    # Load all the details we need from the source profile, the one with the actual user and keys
    user_profile=$(aws configure get ${target_profile}.source_profile)
    : ${user_profile:?}
    export AWS_ACCESS_KEY_ID=$(aws configure get ${user_profile}.aws_access_key_id)
    export AWS_SECRET_ACCESS_KEY=$(aws configure get ${user_profile}.aws_secret_access_key)
    export AWS_PROFILE=${target_profile}

    # Load details about the role we need to assume in the target profile
    role_arn=$(aws configure get ${target_profile}.role_arn)
    mfa_serial=$(aws configure get ${target_profile}.mfa_serial)
    role_session_name=$(get_role_session_name)

    # Assume role with or without an MFA device
    eval $(aws sts assume-role \
        ${mfa_serial:+ --serial-number $mfa_serial} \
        ${mfa_code:+ --token-code ${mfa_code}} \
        --role-arn ${role_arn} \
        --role-session-name "${role_session_name}" \
        --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' | jq '"export AWS_ACCESS_KEY_ID=" + .[0] + "; export AWS_SECRET_ACCESS_KEY=" + .[1] + "; export AWS_SESSION_TOKEN=" + .[2] + ";"' --raw-output)
    if [ -n "${AWS_SESSION_TOKEN}" ] ; then
        echo Successfully assumed role \"${role_arn}\" as session \"${role_session_name}\" using profile \"${target_profile}\" ${mfa_serial:+ with MFA device \"${mfa_serial}\"}
    fi
}

cz_assert_profile(){
  local role_session_name=$(get_role_session_name)
  echo ${role_session_name}
  aws sts get-caller-identity |
    jq -r -e '.Arn' |
    grep -e "^arn:aws:sts::\([0-9]\{12\}\):assumed-role/\([A-Za-z\-]\+\)/${role_session_name}$" ||
    { echo "Not in a cz_use_profile assumed role!" ; return 1 ; }
}

# Clear environment variables from a previous call to use-profile
cz_clear_profile() {
    unset AWS_SESSION_TOKEN
    unset AWS_SECRET_ACCESS_KEY
    unset AWS_ACCESS_KEY_ID
    unset AWS_SECURITY_TOKEN
    unset AWS_PROFILE
}

# Shows the currently applied AWS profile details.
# NOTE: Credentials shown here might be expired; if they are, run use_profile again.
cz_show_profile() {
    printenv | grep AWS_
}
