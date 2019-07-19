# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

from pprint import pformat
import boto3
import cfnresponse
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, ExactSequence, Schema, ALLOW_EXTRA, REMOVE_EXTRA


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


sqs = boto3.resource('sqs')

DEFAULT_OUTPUT = {
}


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        'RequestType': Any('Create', 'Update', 'Delete'),
        'ResourceProperties': dict,
        'ResponseURL': str,
        'StackId': str
    }
}, required=True, extra=REMOVE_EXTRA)

OUTPUT_SCHEMA = Schema({
    'output': dict,
}, required=True, extra=ALLOW_EXTRA)

event_account_id = get_in(['event', 'ResourceProperties', 'AccountId'])


#####################
#
# Coeffects, i.e. from the outside world
#
#####################
def coeffects(world):
    return pipe(world)


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


#####################
#
# Business Logic
#
#####################
def notify_cloudzero(world):
    return pipe(world)


#####################
#
# Effects, i.e. changes to the outside world
#
#####################
def effects(world):
    return pipe(world)


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
                     notify_cloudzero,
                     effects,
                     OUTPUT_SCHEMA)
        logger.info(f'Finished Processing: {pformat(world)}')
    except Exception as err:
        logger.exception(err)
    finally:
        output = world.get('output', DEFAULT_OUTPUT)
        logger.info(f'Sending output {pformat(output)}')
        cfnresponse.send(event, context, status, output, event.get('PhysicalResourceId'))
