# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

"""
NotifyCloudZero custom-resource handler.

Posts the result of account provisioning back to the CloudZero reactor. The parent
stack passes every value this needs directly as resource properties (resolved from
`!GetAtt` of the Discovery resource and the AccountResources nested stack), so this
handler no longer reads sibling CloudFormation stack outputs at runtime -- it just
reshapes the properties into the reactor payload and POSTs it.

IMPORTANT: the reactor payload (`account-link-provisioned` / `-deprovisioned`) is a
FIXED external contract. Do not add, rename, or drop keys. The audit and
cloudtrail-owner account types are deprecated, but their keys remain in the payload
and are emitted as null / no-op values.
"""

import json
import logging

import urllib3
from voluptuous import Any, Match, Schema, ALLOW_EXTRA, REMOVE_EXTRA

from src import cfnresponse

http = urllib3.PoolManager()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_BILLING_REPORT_FORMAT = 'aws'


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        'RequestType': Any('Create', 'Delete', 'Update'),
        'ResourceProperties': {
            # Reactor / account metadata
            'ExternalId': str,
            'ReactorCallbackUrl': str,
            'AccountName': str,
            'ReactorId': str,
            'AccountId': str,
            'Region': str,
            # Discovery flags (arrive as the strings 'true' / 'false')
            'IsResourceOwnerAccount': str,
            'IsMasterPayerAccount': str,
            'IsOrganizationMasterAccount': str,
            # Provisioned role ARNs ('null' when that account type wasn't provisioned)
            'ResourceOwnerRoleArn': str,
            'MasterPayerRoleArn': str,
            # Master-payer billing details
            'MasterPayerBillingBucketName': str,
            'MasterPayerBillingBucketPath': str,
            'MasterPayerReportS3Bucket': str,
            'MasterPayerReportS3Prefix': str,
            'BillingReportFormat': str,
        },
        'ResponseURL': str,
        'StackId': str,
    }
}, required=True, extra=REMOVE_EXTRA)

ARN = Schema(Match(r'^arn:(?:aws|aws-cn|aws-us-gov):([a-z0-9-]+):'
                   r'((?:[a-z0-9-]*)|global):(\d{12}|aws)*:(.+$)$'))
NONEABLE_ARN = Schema(Any(None, ARN))
NONEABLE_BOOL = Schema(Any(None, bool))
NONEABLE_STRING = Schema(Any(None, str))
LINK_ROLE = Schema({'role_arn': NONEABLE_ARN})

# The reactor payload contract. FIXED -- do not change its shape.
ACCOUNT_LINK_PROVISIONED = Schema({
    'data': {
        'metadata': {
            'cloud_region': str,
            'external_id': str,
            'cloud_account_id': str,
            'cz_account_name': str,
            'reactor_id': str,
            'reactor_callback_url': str,
            'billing_report_format': NONEABLE_STRING,
        },
        'links': {
            'audit': LINK_ROLE,
            'cloudtrail_owner': {
                'sqs_queue_arn': NONEABLE_ARN,
                'sqs_queue_policy_name': NONEABLE_STRING,
            },
            'master_payer': LINK_ROLE,
            'resource_owner': LINK_ROLE,
            'legacy': LINK_ROLE,
        },
        'discovery': {
            'audit_cloudtrail_bucket_name': NONEABLE_STRING,
            'audit_cloudtrail_bucket_prefix': NONEABLE_STRING,
            'cloudtrail_sns_topic_arn': NONEABLE_ARN,
            'cloudtrail_trail_arn': NONEABLE_ARN,
            'is_audit_account': bool,
            'is_cloudtrail_owner_account': bool,
            'is_organization_trail': NONEABLE_BOOL,
            'is_organization_master_account': bool,
            'is_master_payer_account': bool,
            'is_resource_owner_account': bool,
            'master_payer_billing_bucket_name': NONEABLE_STRING,
            'master_payer_billing_bucket_path': NONEABLE_STRING,
            'remote_cloudtrail_bucket': bool,
        }
    }
}, required=True, extra=ALLOW_EXTRA)

OUTPUT_SCHEMA = Schema({'output': ACCOUNT_LINK_PROVISIONED}, required=True, extra=ALLOW_EXTRA)


#####################
#
# Property coercion (CloudFormation passes every property as a string)
#
#####################
def to_value(s):
    """Treat 'null'/empty as absent; otherwise return the string unchanged."""
    return None if s in (None, '', 'null') else s


def to_bool(s):
    """Coerce a CloudFormation string flag to a strict bool ('true' -> True, else False)."""
    return str(s).lower() == 'true'


#####################
#
# Business Logic
#
#####################
def build_payload(properties, message_type):
    """Reshape the resource properties into the fixed reactor payload."""
    resource_owner_role_arn = to_value(properties['ResourceOwnerRoleArn'])
    master_payer_role_arn = to_value(properties['MasterPayerRoleArn'])
    # An existing CUR reports its bucket via discovery; a freshly created CUR reports it
    # via the master-payer report outputs. Prefer the discovered one.
    billing_bucket_name = to_value(properties['MasterPayerBillingBucketName']) or \
        to_value(properties['MasterPayerReportS3Bucket'])
    billing_bucket_path = to_value(properties['MasterPayerBillingBucketPath']) or \
        to_value(properties['MasterPayerReportS3Prefix'])

    return {
        'version': '1',
        'message_source': 'cfn',
        'message_type': message_type,
        'data': {
            'metadata': {
                'cloud_region': properties['Region'],
                'external_id': properties['ExternalId'],
                'cloud_account_id': properties['AccountId'],
                'cz_account_name': properties['AccountName'],
                'reactor_id': properties['ReactorId'],
                'reactor_callback_url': properties['ReactorCallbackUrl'],
                'billing_report_format': to_value(properties['BillingReportFormat']) or DEFAULT_BILLING_REPORT_FORMAT,
            },
            'links': {
                # audit + cloudtrail_owner are deprecated: their slots remain in the
                # fixed contract but are always null/no-op now.
                'audit': {'role_arn': None},
                'cloudtrail_owner': {'sqs_queue_arn': None, 'sqs_queue_policy_name': None},
                'master_payer': {'role_arn': master_payer_role_arn},
                'resource_owner': {'role_arn': resource_owner_role_arn},
                'legacy': {'role_arn': resource_owner_role_arn},
            },
            'discovery': {
                # Deprecated cloudtrail/audit discovery fields -- retained as null/no-op
                # for contract stability (see module docstring).
                'audit_cloudtrail_bucket_name': None,
                'audit_cloudtrail_bucket_prefix': None,
                'cloudtrail_sns_topic_arn': None,
                'cloudtrail_trail_arn': None,
                'is_audit_account': False,
                'is_cloudtrail_owner_account': False,
                'is_organization_trail': None,
                'remote_cloudtrail_bucket': True,
                'visible_cloudtrail_arns': None,
                # Live discovery values
                'is_master_payer_account': to_bool(properties['IsMasterPayerAccount']),
                'is_organization_master_account': to_bool(properties['IsOrganizationMasterAccount']),
                'is_resource_owner_account': to_bool(properties['IsResourceOwnerAccount']),
                'master_payer_billing_bucket_name': billing_bucket_name,
                'master_payer_billing_bucket_path': billing_bucket_path,
            }
        }
    }


def message_type_for(request_type):
    return 'account-link-provisioned' if request_type in {'Create', 'Update'} else 'account-link-deprovisioned'


#####################
#
# Effects, i.e. changes to the outside world
#
#####################
def post_to_reactor(url, payload):
    body = json.dumps(payload)
    logger.info(f'Posting to {url} this data: {body}')
    response = http.request('POST', url, body=body.encode('utf-8'))
    response_text = response.data.decode('utf-8')
    logger.info(f'response {response.status}; text {response_text}')
    assert response.status == 200
    return response_text


#####################
#
# Handler
#
#####################
def handler(event, context, **kwargs):
    status = cfnresponse.SUCCESS
    payload = {}
    try:
        logger.info(f'Processing event {json.dumps(event)}')
        validated = INPUT_SCHEMA({'event': event})['event']
        properties = validated['ResourceProperties']
        payload = build_payload(properties, message_type_for(validated['RequestType']))
        OUTPUT_SCHEMA({'output': payload})  # validate the fixed contract before sending
        post_to_reactor(properties['ReactorCallbackUrl'], payload)
    except Exception as err:
        logger.exception(err)
    finally:
        cfnresponse.send(event, context, status, payload, event.get('PhysicalResourceId'))
