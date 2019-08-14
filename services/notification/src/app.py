# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import boto3
import cfnresponse
import requests
import simplejson as json
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, Invalid, Match, Optional, Schema, ALLOW_EXTRA, REMOVE_EXTRA


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

cfn = boto3.resource('cloudformation')

DEFAULT_CFN_COEFFECT = {
    'AuditAccount': {
        'RoleArn': 'null',
    },
    'CloudTrailOwnerAccount': {
        'SQSQueueArn': 'null',
        'SQSQueuePolicyArn': 'null'
    },
    'Discovery': {
        'AuditCloudTrailBucketName': 'null',
        'MasterPayerBillingBucketName': 'null',
        'CloudTrailSNSTopicArn': 'null',
        'IsCloudTrailOwnerAccount': 'false',
        'IsMasterPayerAccount': 'false',
        'IsAuditAccount': 'false',
        'IsResourceOwnerAccount': 'false'
    },
    'MasterPayerAccount': {
        'RoleArn': 'null',
    },
    'ResourceOwnerAccount': {
        'RoleArn': 'null'
    },
    'LegacyAccount': {
        'RoleArn': 'null'
    }
}


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        'RequestType': Any('Create', 'Update', 'Delete'),
        'ResourceProperties': {
            'ExternalId': str,
            'ReactorCallbackUrl': str,
            'AccountName': str,
            'ReactorId': str,
            'AccountId': str,
            'Region': str,
            'Stacks': {
                'Discovery': str,
                'ResourceOwnerAccount': str,
                'CloudTrailOwnerAccount': str,
                'AuditAccount': str,
                'MasterPayerAccount': str,
                'LegacyAccount': str,
            }
        },
        'ResponseURL': str,
        'StackId': str
    }
}, required=True, extra=REMOVE_EXTRA)

STRING_TRUE_FALSE = Schema(Any('true', 'false'))
ARN = Schema(Match(r'^arn:(?:aws|aws-cn|aws-us-gov):([a-z0-9-]+):'
                   r'((?:[a-z0-9-]*)|global):(\d{12}|aws)*:(.+$)$'))
NULLABLE_ARN = Schema(Any('null', ARN))

CFN_COEFFECT_SCHEMA = Schema({
    'AuditAccount': {
        'RoleArn': NULLABLE_ARN
    },
    'CloudTrailOwnerAccount': {
        'SQSQueueArn': NULLABLE_ARN,
        'SQSQueuePolicyArn': NULLABLE_ARN,
    },
    'Discovery': {
        'AuditCloudTrailBucketName': NULLABLE_ARN,
        'MasterPayerBillingBucketName': NULLABLE_ARN,
        'CloudTrailSNSTopicArn': NULLABLE_ARN,
        'IsCloudTrailOwnerAccount': STRING_TRUE_FALSE,
        'IsMasterPayerAccount': STRING_TRUE_FALSE,
        'IsAuditAccount': STRING_TRUE_FALSE,
        'IsResourceOwnerAccount': STRING_TRUE_FALSE,
    },
    'MasterPayerAccount': {
        'RoleArn': NULLABLE_ARN,
    },
    'ResourceOwnerAccount': {
        'RoleArn': NULLABLE_ARN,
    },
    'LegacyAccount': {
        'RoleArn': NULLABLE_ARN,
    }
})


NONEABLE_ARN = Schema(Any(None, ARN))
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
                'sqs_queue_policy_arn': NONEABLE_ARN,
            },
            'master_payer': LINK_ROLE,
            'resource_owner': LINK_ROLE,
            'legacy': LINK_ROLE,
        },
        'discovery': {
            'audit_cloudtrail_bucket_name': Any(None, str),
            'cloudtrail_sns_topic_arn': NONEABLE_ARN,
            'master_payer_billing_bucket_name': Any(None, str),
            'is_audit_account': bool,
            'is_cloudtrail_owner_account': bool,
            'is_master_payer_account': bool,
            'is_resource_owner_account': bool,
        }
    }
}, required=True, extra=ALLOW_EXTRA)

OUTPUT_SCHEMA = Schema({
    'output': ACCOUNT_LINK_PROVISIONED,
}, required=True, extra=ALLOW_EXTRA)


properties = get_in(['event', 'ResourceProperties'])
stacks = get_in(['event', 'ResourceProperties', 'Stacks'])
reactor_callback_url = get_in(['event', 'ResourceProperties', 'ReactorCallbackUrl'])
supported_metadata = {'Region', 'ExternalId', 'AccountId', 'AccountName', 'ReactorId', 'ReactorCallbackUrl'}
callback_metadata = keyfilter(lambda x: x in supported_metadata)
default_metadata = {
    'version': '1',
    'message_source': 'cfn',
    'message_type': 'account-link-provisioned',
}


#####################
#
# Coeffects, i.e. from the outside world
#
#####################
def coeffects(world):
    return pipe(world,
                coeffects_cfn)


def coeffect(name):
    def d(f):
        def w(world):
            data = {}
            try:
                data = f(world)
            except Exception:
                logger.warning(f'Failed to get {name} information.', exc_info=True)
            return assoc_in(world, ['coeffects', name], data)
        return w
    return d


def outputs_to_dict(outputs):
    return {
        output['OutputKey']: output['OutputValue']
        for output in outputs or []
    }


@coeffect('cloudformation')
def coeffects_cfn(world):
    return {
        key: outputs_to_dict(cfn.Stack(name).outputs)
        for key, name in stacks(world, default={}).items()
    }


#####################
#
# Business Logic
#
#####################
def notify_cloudzero(world):
    return pipe(world,
                validate_cfn_coeffect,
                prepare_output)


def validate_cfn_coeffect(world):
    cfn_coeffect = get_in(['coeffects', 'cloudformation'], world)
    try:
        return update_in(world, ['valid_cfn'],
                         lambda x: merge(x or {}, CFN_COEFFECT_SCHEMA(cfn_coeffect)))
    except Invalid:
        logger.warning('CloudFormation Coeffects are not valid; using defaults')
        return update_in(world, ['valid_cfn'],
                         lambda x: merge(x or {}, DEFAULT_CFN_COEFFECT))


def null_to_none(s):
    return None if s == 'null' else s


def string_to_bool(s):
    return s == 'true'


def prepare_output(world):
    valid_cfn = get_in(['valid_cfn'], world)
    metadata = callback_metadata(properties(world))
    output = {
        **default_metadata,
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
                'audit': {'role_arn': null_to_none(get_in(['AuditAccount', 'RoleArn'], valid_cfn))},
                'cloudtrail_owner': {
                    'sqs_queue_arn': null_to_none(get_in(['CloudTrailOwnerAccount', 'SQSQueueArn'], valid_cfn)),
                    'sqs_queue_policy_arn': null_to_none(get_in(['CloudTrailOwnerAccount', 'SQSQueuePolicyArn'], valid_cfn)),
                },
                'master_payer': {'role_arn': null_to_none(get_in(['MasterPayerAccount', 'RoleArn'], valid_cfn))},
                'resource_owner': {'role_arn': null_to_none(get_in(['ResourceOwnerAccount', 'RoleArn'], valid_cfn))},
                'legacy': {'role_arn': null_to_none(get_in(['LegacyAccount', 'RoleArn'], valid_cfn))},
            },
            'discovery': {
                'audit_cloudtrail_bucket_name': null_to_none(get_in(['Discovery', 'AuditCloudTrailBucketName'], valid_cfn)),
                'cloudtrail_sns_topic_arn': null_to_none(get_in(['Discovery', 'CloudTrailSNSTopicArn'], valid_cfn)),
                'master_payer_billing_bucket_name': null_to_none(get_in(['Discovery', 'MasterPayerBillingBucketName'], valid_cfn)),
                'is_audit_account': string_to_bool(get_in(['Discovery', 'IsAuditAccount'], valid_cfn)),
                'is_cloudtrail_owner_account': string_to_bool(get_in(['Discovery', 'IsCloudTrailOwnerAccount'], valid_cfn)),
                'is_master_payer_account': string_to_bool(get_in(['Discovery', 'IsMasterPayerAccount'], valid_cfn)),
                'is_resource_owner_account': string_to_bool(get_in(['Discovery', 'IsResourceOwnerAccount'], valid_cfn)),
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
    logger.info(f'Posting to {url} this data: {json.dumps(data)}')
    response = requests.post(url, json=data)
    logger.info(f'response {response.status_code}; text {response.text}')
    assert response.status_code == 200
    return response.text


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
                     coeffects,
                     notify_cloudzero,
                     effects,
                     OUTPUT_SCHEMA)
    except Exception as err:
        logger.exception(err)
    finally:
        output = world.get('output')
        logger.info(f'Sending output {output}')
        cfnresponse.send(event, context, status, output, event.get('PhysicalResourceId'))
