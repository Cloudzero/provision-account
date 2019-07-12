# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

from pprint import pformat
import boto3
import cfnresponse
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, Schema, ALLOW_EXTRA, REMOVE_EXTRA


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


ct = boto3.client('cloudtrail')
cur = boto3.client('cur')
s3 = boto3.client('s3')

DEFAULT_OUTPUT = {
    'IsAuditAccount': False,
    'AuditCloudTrailBucketName': None,
    'IsConnectedAccount': False,
    'IsCloudTrailAccount': False,
    'CloudTrailSNSTopicName': None,
    'IsMasterPayerAccount': False,
    'MasterPayerBillingBucketName': None,
}


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        # 'LogicalResourceId': str,
        # 'PhysicalResourceId': Any(None, str),
        # 'RequestId': str,
        'RequestType': Any('Create', 'Update', 'Delete'),
        'ResourceProperties': {
            'AccountId': str
        },
        'ResponseURL': str,
        'StackId': str
    }
}, required=True, extra=REMOVE_EXTRA)

OUTPUT_SCHEMA = Schema({
    'output': {
        'IsAuditAccount': bool,
        'AuditCloudTrailBucketName': Any(None, str),
        'IsConnectedAccount': bool,
        'IsCloudTrailAccount': bool,
        'CloudTrailSNSTopicName': Any(None, str),
        'IsMasterPayerAccount': bool,
        'MasterPayerBillingBucketName': Any(None, str),
    },
}, required=True, extra=ALLOW_EXTRA)

event_account_id = get_in(['event', 'ResourceProperties', 'AccountId'])


#####################
#
# Coeffects, i.e. from the outside world
#
#####################
def coeffects(world):
    return pipe(world,
                coeffects_cloudtrail,
                coeffects_s3,
                coeffects_cur)


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


@coeffect('cloudtrail')
def coeffects_cloudtrail(world):
    response = ct.describe_trails()
    return keyfilter(lambda x: x in {'trailList'}, response)


@coeffect('s3')
def coeffects_s3(world):
    response = s3.list_buckets()
    return keyfilter(lambda x: x in {'Buckets'}, response)


@coeffect('cur')
def coeffects_cur(world):
    response = cur.describe_report_definitions()
    return keyfilter(lambda x: x in {'ReportDefinitions'}, response)


#####################
#
# Business Logic
#
#####################
def audit(world):
    account_id = event_account_id(world)
    trail_bucket = get_in(['coeffects', 'cloudtrail', 'trailList', 0, 'S3BucketName'], world)
    local_buckets = {x['Name'] for x in get_in(['coeffects', 's3', 'Buckets'], world, [])}
    output = {
        'IsAuditAccount': trail_bucket in local_buckets,
        'AuditCloudTrailBucketName': trail_bucket,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def connected(world):
    output = {
        'IsConnectedAccount': True,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def cloudtrail(world):
    trail_topic = get_in(['coeffects', 'cloudtrail', 'trailList', 0, 'SnsTopicName'], world)
    account_id = trail_topic.split(':')[4]
    output = {
        'IsCloudTrailAccount': account_id == event_account_id(world),
        'CloudTrailSNSTopicName': trail_topic,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def master_payer(world):
    account_id = event_account_id(world)
    payer_bucket = get_in(['coeffects', 'cur', 'ReportDefinitions', 0, 'S3Bucket'], world)
    local_buckets = {x['Name'] for x in get_in(['coeffects', 's3', 'Buckets'], world, [])}
    output = {
        'IsMasterPayerAccount': payer_bucket in local_buckets,
        'MasterPayerBillingBucketName': payer_bucket,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def discover_account_types(world):
    return pipe(world,
                audit,
                connected,
                cloudtrail,
                master_payer)


#####################
#
# Handler
#
#####################
def handler(event, context, **kwargs):
    status = cfnresponse.SUCCESS
    world = {}
    try:
        logger.info(f'Processing event {pformat(event)}')
        world = pipe({'event': event, 'kwargs': kwargs},
                     INPUT_SCHEMA,
                     coeffects,
                     discover_account_types,
                     OUTPUT_SCHEMA)
        logger.info(f'Finished Processing: {pformat(world)}')
    except Exception as err:
        logger.exception(err)
    finally:
        output = world.get('output', DEFAULT_OUTPUT)
        output['String'] = 'foo'
        logger.info(f'Sending output {pformat(output)}')
        cfnresponse.send(event, context, status, output, event.get('PhysicalResourceId'))
