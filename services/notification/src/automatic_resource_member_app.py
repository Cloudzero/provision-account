# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import logging
import json

import boto3
import urllib3
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, Match, Schema, ALLOW_EXTRA, REMOVE_EXTRA

from src import cfnresponse

cfn = boto3.resource('cloudformation')
http = urllib3.PoolManager()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


DEFAULT_CFN_COEFFECT = {
    'AuditAccount': {
        'AuditRoleArn': 'null',
    },
    'CloudTrailOwnerAccount': {
        'SQSQueueArn': 'null',
        'SQSQueuePolicyName': 'null'
    },
    'Discovery': {
        'AuditCloudTrailBucketName': 'null',
        'AuditCloudTrailBucketPrefix': 'null',
        'CloudTrailSNSTopicArn': 'null',
        'CloudTrailTrailArn': 'null',
        'VisibleCloudTrailArns': 'null',
        'IsAuditAccount': 'false',
        'IsCloudTrailOwnerAccount': 'false',
        'IsMasterPayerAccount': 'false',
        'IsOrganizationMasterAccount': 'false',
        'IsOrganizationTrail': 'null',
        'IsResourceOwnerAccount': 'false',
        'MasterPayerBillingBucketName': 'null',
        'MasterPayerBillingBucketPath': 'null',
        'RemoteCloudTrailBucket': 'true',
    },
    'MasterPayerAccount': {
        'MasterPayerRoleArn': 'null',
        'ReportS3Bucket': 'null',
        'ReportS3Prefix': 'null',
    },
    'ResourceOwnerAccount': {
        'ResourceOwnerRoleArn': 'null'
    },
    'LegacyAccount': {
        'ResourceOwnerRoleArn': 'null'
    }
}


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        'RequestType': Any('Create', 'Delete', 'Update'),
        'ResourceProperties': {
            'ExternalId': str,
            'ReactorCallbackUrl': str,
            'AccountName': str,
            'ReactorId': str,
            'AccountId': str,
            'Region': str,
            'ResourceOwnerRoleArn': str
        },
        'ResponseURL': str,
        'StackId': str
    }
}, required=True, extra=REMOVE_EXTRA)

BOOLEAN_STRING = Schema(Any('null', 'true', 'false'))
ARN = Schema(Match(r'^arn:(?:aws|aws-cn|aws-us-gov):([a-z0-9-]+):'
                   r'((?:[a-z0-9-]*)|global):(\d{12}|aws)*:(.+$)$'))
NULLABLE_ARN = Schema(Any('null', ARN))
NULLABLE_STRING = Schema(Any('null', str))
NONEABLE_ARN = Schema(Any(None, ARN))
NONEABLE_BOOL = Schema(Any(None, bool))
NONEABLE_STRING = Schema(Any(None, str))
LINK_ROLE = Schema({'role_arn': NONEABLE_ARN})
ACCOUNT_LINK_PROVISIONED = Schema({
    'data': {
        'metadata': {
            'cloud_region': str,
            'external_id': str,
            'cloud_account_id': str,
            'cz_account_name': str,
            'reactor_id': str,
            'reactor_callback_url': str,
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

OUTPUT_SCHEMA = Schema({
    'output': ACCOUNT_LINK_PROVISIONED,
}, required=True, extra=ALLOW_EXTRA)


request_type = get_in(['event', 'RequestType'])
properties = get_in(['event', 'ResourceProperties'])
stacks = get_in(['event', 'ResourceProperties', 'Stacks'])
reactor_callback_url = get_in(['event', 'ResourceProperties', 'ReactorCallbackUrl'])
supported_metadata = {'Region', 'ExternalId', 'AccountId', 'AccountName', 'ReactorId', 'ReactorCallbackUrl', 'ResourceOwnerRoleArn'}
callback_metadata = keyfilter(lambda x: x in supported_metadata)
default_metadata = {
    'version': '1',
    'message_source': 'cfn',
}


#####################
#
# Business Logic
#
#####################
def notify_cloudzero(world):
    return pipe(world, prepare_output)


def prepare_output(world):
    metadata = callback_metadata(properties(world))
    message_type = 'account-link-provisioned' if request_type(world) in {'Create', 'Update'} else 'account-link-deprovisioned'

    output = {
        **default_metadata,
        'message_type': message_type,
        'data': {
            'metadata': {
                'cloud_region': metadata['Region'],
                'external_id': metadata['ExternalId'],
                'cloud_account_id': metadata['AccountId'],
                'cz_account_name': metadata['AccountName'],
                'reactor_id': metadata['ReactorId'],
                'reactor_callback_url': metadata['ReactorCallbackUrl'],
            },
            'links': {
                'audit': {'role_arn': None},
                'cloudtrail_owner': {
                    'sqs_queue_arn': None,
                    'sqs_queue_policy_name': None,
                },
                'master_payer': {'role_arn': None},
                'resource_owner': {'role_arn': metadata['ResourceOwnerRoleArn']},
                'legacy': {'role_arn': metadata['ResourceOwnerRoleArn']},
            },
            'discovery': {
                'audit_cloudtrail_bucket_name': None,
                'audit_cloudtrail_bucket_prefix': None,
                'cloudtrail_sns_topic_arn': None,
                'cloudtrail_trail_arn': None,
                'is_audit_account': False,
                'is_cloudtrail_owner_account': False,
                'is_master_payer_account': False,
                'is_organization_master_account': False,
                'is_organization_trail': False,
                'is_resource_owner_account': True,
                'master_payer_billing_bucket_name': None,
                'master_payer_billing_bucket_path': None,
                'remote_cloudtrail_bucket': False,
                'visible_cloudtrail_arns': None,
            }
        }
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


#####################
#
# Effects, i.e. changes to the outside world
#
#####################
def effects(world):
    return pipe(world,
                effects_reactor_callback)


def effect(name):
    def d(f):
        def w(world):
            data = {}
            try:
                data = f(world)
            except Exception:
                logger.warning(f'Failed to effect {name} change.', exc_info=True)
            return assoc_in(world, ['effects', name], data)
        return w
    return d


@effect('reactor')
def effects_reactor_callback(world):
    url = reactor_callback_url(world)
    data = get_in(['output'], world)
    data_string = json.dumps(data)
    logger.info(f'Posting to {url} this data: {data_string}')
    response = http.request('POST', url, body=data_string.encode('utf-8'))
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
    world = {}
    try:
        logger.info(f'Processing event {json.dumps(event)}')
        world = pipe({'event': event, 'kwargs': kwargs},
                     INPUT_SCHEMA,
                     notify_cloudzero,
                     effects,
                     OUTPUT_SCHEMA)
    except Exception as err:
        logger.exception(err)
    finally:
        output = world.get('output')
        logger.info(f'Sending output {output}')
        cfnresponse.send(event, context, status, output, event.get('PhysicalResourceId'))
