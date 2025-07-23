# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import logging
import json

import boto3
import urllib3
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, Invalid, Match, Schema, ALLOW_EXTRA, REMOVE_EXTRA

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
        'LegacyRoleArn': 'null'
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

BOOLEAN_STRING = Schema(Any('null', 'true', 'false'))
ARN = Schema(Match(r'^arn:(?:aws|aws-cn|aws-us-gov):([a-z0-9-]+):'
                   r'((?:[a-z0-9-]*)|global):(\d{12}|aws)*:(.+$)$'))
NULLABLE_ARN = Schema(Any('null', ARN))
NULLABLE_STRING = Schema(Any('null', str))

CFN_COEFFECT_SCHEMA = Schema({
    'AuditAccount': {
        'AuditRoleArn': NULLABLE_ARN
    },
    'CloudTrailOwnerAccount': {
        'SQSQueueArn': NULLABLE_ARN,
        'SQSQueuePolicyName': NULLABLE_STRING,
    },
    'Discovery': {
        'AuditCloudTrailBucketName': NULLABLE_STRING,
        'AuditCloudTrailBucketPrefix': NULLABLE_STRING,
        'CloudTrailSNSTopicArn': NULLABLE_ARN,
        'CloudTrailTrailArn': NULLABLE_ARN,
        'VisibleCloudTrailArns': NULLABLE_STRING,
        'IsAuditAccount': BOOLEAN_STRING,
        'IsCloudTrailOwnerAccount': BOOLEAN_STRING,
        'IsMasterPayerAccount': BOOLEAN_STRING,
        'IsOrganizationMasterAccount': BOOLEAN_STRING,
        'IsOrganizationTrail': BOOLEAN_STRING,
        'IsResourceOwnerAccount': BOOLEAN_STRING,
        'MasterPayerBillingBucketName': NULLABLE_STRING,
        'MasterPayerBillingBucketPath': NULLABLE_STRING,
        'RemoteCloudTrailBucket': BOOLEAN_STRING,
    },
    'MasterPayerAccount': {
        'MasterPayerRoleArn': NULLABLE_ARN,
        'ReportS3Bucket': NULLABLE_STRING,
        'ReportS3Prefix': NULLABLE_STRING,
    },
    'ResourceOwnerAccount': {
        'ResourceOwnerRoleArn': NULLABLE_ARN,
    },
    'LegacyAccount': {
        'LegacyRoleArn': NULLABLE_ARN,
    }
}, required=True, extra=ALLOW_EXTRA)


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
supported_metadata = {'Region', 'ExternalId', 'AccountId', 'AccountName', 'ReactorId', 'ReactorCallbackUrl'}
callback_metadata = keyfilter(lambda x: x in supported_metadata)
default_metadata = {
    'version': '1',
    'message_source': 'cfn',
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
        logger.warning(cfn_coeffect)
        logger.warning('CloudFormation Coeffects are not valid; using defaults', exc_info=True)
        return update_in(world, ['valid_cfn'],
                         lambda x: merge(x or {}, DEFAULT_CFN_COEFFECT))


def null_to_none(s):
    return None if s == 'null' else s


def string_to_bool(s):
    """
    Convert String to Bool

    >>> string_to_bool('True')
    True

    >>> string_to_bool('true')
    True

    >>> string_to_bool('False')
    False

    >>> string_to_bool('false')
    False

    >>> string_to_bool('null')

    >>> string_to_bool(None)

    >>> string_to_bool('')

    """
    if not s:
        return None
    return None if s.lower() == 'null' else s.lower() == 'true'


def prepare_output(world):
    valid_cfn = get_in(['valid_cfn'], world)
    metadata = callback_metadata(properties(world))
    message_type = 'account-link-provisioned' if request_type(world) in {'Create', 'Update'} else 'account-link-deprovisioned'
    visible_cloudtrail_arns_string = null_to_none(get_in(['Discovery', 'VisibleCloudTrailArns'], valid_cfn))
    visible_cloudtrail_arns = visible_cloudtrail_arns_string.split(',') if visible_cloudtrail_arns_string else None
    master_payer_billing_bucket_name = (null_to_none(get_in(['Discovery', 'MasterPayerBillingBucketName'], valid_cfn)) or
                                        null_to_none(get_in(['MasterPayerAccount', 'ReportS3Bucket'], valid_cfn)))
    master_payer_billing_bucket_path = (null_to_none(get_in(['Discovery', 'MasterPayerBillingBucketPath'], valid_cfn)) or
                                        null_to_none(get_in(['MasterPayerAccount', 'ReportS3Prefix'], valid_cfn)))
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
                'audit': {'role_arn': null_to_none(get_in(['AuditAccount', 'AuditRoleArn'], valid_cfn))},
                'cloudtrail_owner': {
                    'sqs_queue_arn': null_to_none(get_in(['CloudTrailOwnerAccount', 'SQSQueueArn'], valid_cfn)),
                    'sqs_queue_policy_name': null_to_none(get_in(['CloudTrailOwnerAccount', 'SQSQueuePolicyName'], valid_cfn)),
                },
                'master_payer': {'role_arn': null_to_none(get_in(['MasterPayerAccount', 'MasterPayerRoleArn'], valid_cfn))},
                'resource_owner': {'role_arn': null_to_none(get_in(['ResourceOwnerAccount', 'ResourceOwnerRoleArn'], valid_cfn))},
                'legacy': {'role_arn': null_to_none(get_in(['LegacyAccount', 'ResourceOwnerRoleArn'], valid_cfn))},
            },
            'discovery': {
                'audit_cloudtrail_bucket_name': null_to_none(get_in(['Discovery', 'AuditCloudTrailBucketName'], valid_cfn)),
                'audit_cloudtrail_bucket_prefix': null_to_none(get_in(['Discovery', 'AuditCloudTrailBucketPrefix'], valid_cfn)),
                'cloudtrail_sns_topic_arn': null_to_none(get_in(['Discovery', 'CloudTrailSNSTopicArn'], valid_cfn)),
                'cloudtrail_trail_arn': null_to_none(get_in(['Discovery', 'CloudTrailTrailArn'], valid_cfn)),

                'is_audit_account': string_to_bool(get_in(['Discovery', 'IsAuditAccount'], valid_cfn)),
                'is_cloudtrail_owner_account': string_to_bool(get_in(['Discovery', 'IsCloudTrailOwnerAccount'], valid_cfn)),
                'is_master_payer_account': string_to_bool(get_in(['Discovery', 'IsMasterPayerAccount'], valid_cfn)),
                'is_organization_master_account': string_to_bool(get_in(['Discovery', 'IsOrganizationMasterAccount'], valid_cfn)),
                'is_organization_trail': string_to_bool(get_in(['Discovery', 'IsOrganizationTrail'], valid_cfn)),
                'is_resource_owner_account': string_to_bool(get_in(['Discovery', 'IsResourceOwnerAccount'], valid_cfn)),
                'master_payer_billing_bucket_name': master_payer_billing_bucket_name,
                'master_payer_billing_bucket_path': master_payer_billing_bucket_path,
                'remote_cloudtrail_bucket': string_to_bool(get_in(['Discovery', 'RemoteCloudTrailBucket'], valid_cfn)),
                'visible_cloudtrail_arns': visible_cloudtrail_arns,
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
