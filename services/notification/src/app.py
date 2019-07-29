# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import boto3
import cfnresponse
import requests
import simplejson as json
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, Schema, ALLOW_EXTRA, REMOVE_EXTRA


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

cfn = boto3.resource('cloudformation')

DEFAULT_OUTPUT = {
    'AuditAccount': {},
    'CloudTrailOwnerAccount': {
        'SQSQueueArn': 'arn:aws:sqs:us-east-1:461080371632:cz-adam-provision-connected-account-CloudTrailOwnerAccoun-SqsQueue-GNMFW27Q4TUQ',
        'SQSQueuePolicyArn': 'cz-adam-provision-connected-account-CloudTrailOwnerAccou-SqsPolicy-3GVXKLNY0GPJ'
    },
    'Discovery': {
        'AuditCloudTrailBucketName': 'cloudtrail-events-966895021400',
        'MasterPayerBillingBucketName': 'null',
        'CloudTrailSNSTopicArn': 'arn:aws:sns:us-east-1:461080371632:cloudtrail-events',
        'IsCloudTrailOwnerAccount': 'true',
        'IsMasterPayerAccount': 'false',
        'IsAuditAccount': 'false',
        'IsResourceOwnerAccount': 'true'
    },
    'MasterPayerAccount': {},
    'ResourceOwnerAccount': {
        'RoleArn': 'arn:aws:iam::461080371632:role/cloudzero/cz-adam-provision-connected-account-ResourceO-Role-1BKZNPQTUCGDN'
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
            }
        },
        'ResponseURL': str,
        'StackId': str
    }
}, required=True, extra=REMOVE_EXTRA)

OUTPUT_SCHEMA = Schema({
    'output': dict,
}, required=True, extra=ALLOW_EXTRA)


properties = get_in(['event', 'ResourceProperties'])
stacks = get_in(['event', 'ResourceProperties', 'Stacks'])
reactor_callback_url = get_in(['event', 'ResourceProperties', 'ReactorCallbackUrl'])
supported_metadata = {'Region', 'ExternalId', 'AccountId', 'AccountName', 'ReactorId', 'ReactorCallbackUrl'}
callback_metadata = keyfilter(lambda x: x in supported_metadata)


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
                prepare_output)


def prepare_output(world):
    output = get_in(['coeffects', 'cloudformation'], world)
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
    data = {
        **callback_metadata(properties(world)),
        'links': world.get('output', DEFAULT_OUTPUT),
    }
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
        output = world.get('output', DEFAULT_OUTPUT)
        logger.info(f'Sending output {output}')
        cfnresponse.send(event, context, status, output, event.get('PhysicalResourceId'))
