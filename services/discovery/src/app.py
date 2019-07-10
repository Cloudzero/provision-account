# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

from pprint import pformat
import boto3
import cfnresponse
from toolz.curried import assoc_in, get_in, keyfilter, pipe
from voluptuous import Any, Schema, ALLOW_EXTRA, REMOVE_EXTRA


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


ct = boto3.client('cloudtrail')
cur = boto3.client('cur')
s3 = boto3.client('s3')


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        'ResourceProperties': {
            'accountId': str
        },
        'PhysicalResourceId': Any(None, str),
    }
}, required=True, extra=REMOVE_EXTRA)

OUTPUT_SCHEMA = Schema({
    'output': {
        'audit': {
            'accountId': str,
            'cloudTrailBucketName': str
        },
        'connected': {
            'accountId': str,
        },
        'cloudTrail': {
            'accountId': str,
            'snsTopicName': str,
        },
        'masterPayer': {
            'accountId': str,
            'billingBucketName': str,
        },
    },
}, required=True, extra=ALLOW_EXTRA)


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
                logger.warning(f'Failed to get {name} information.')
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
    account_id = get_in(['event', 'ResourceProperties', 'accountId'], world)
    trail_bucket = get_in(['coeffects', 'cloudtrail', 'trailList', 0, 'S3BucketName'], world)
    local_buckets = {x['Name'] for x in get_in(['coeffects', 's3', 'Buckets'], world, [])}
    output = {
        'accountId': account_id if trail_bucket in local_buckets else None,
        'cloudTrailBucketName': trail_bucket,
    }
    return assoc_in(world, ['output', 'audit'], output)


def connected(world):
    output = {
        'accountId': get_in(['event', 'ResourceProperties', 'accountId'], world),
    }
    return assoc_in(world, ['output', 'connected'], output)


def cloudtrail(world):
    trail_topic = get_in(['coeffects', 'cloudtrail', 'trailList', 0, 'SnsTopicName'], world)
    account_id = trail_topic.split(':')[4]
    output = {
        'accountId': account_id,
        'snsTopicName': trail_topic,
    }
    return assoc_in(world, ['output', 'cloudTrail'], output)


def master_payer(world):
    account_id = get_in(['event', 'ResourceProperties', 'accountId'], world)
    payer_bucket = get_in(['coeffects', 'cur', 'ReportDefinitions', 0, 'S3Bucket'], world)
    local_buckets = {x['Name'] for x in get_in(['coeffects', 's3', 'Buckets'], world, [])}
    output = {
        'accountId': account_id if payer_bucket in local_buckets else None,
        'billingBucketName': payer_bucket,
    }
    return assoc_in(world, ['output', 'masterPayer'], output)


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
        world = pipe({'event': event, 'kwargs': kwargs},
                     INPUT_SCHEMA,
                     coeffects,
                     discover_account_types,
                     OUTPUT_SCHEMA)
        print(f'Finished Processing: {pformat(world)}')
    except Exception as err:
        logger.exception(err)
        status = cfnresponse.FAILED
    finally:
        cfnresponse.send(event, context, status, world.get('output', {}), event.get('PhysicalResourceId'))
