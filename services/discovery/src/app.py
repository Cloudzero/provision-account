# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

from pprint import pformat
# import boto3
import cfnresponse
from toolz.curried import assoc_in, pipe
from voluptuous import Any, Schema, ALLOW_EXTRA, REMOVE_EXTRA


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        'ResourceProperties': dict,
        'PhysicalResourceId': Any(None, str),
    }
}, required=True, extra=REMOVE_EXTRA)

OUTPUT_SCHEMA = Schema({
    'output': {
        'isAudit': bool,
        'isConnectable': bool,
        'isCloudTrailOwner': bool,
        'isMasterPayer': bool,
    },
}, required=True, extra=ALLOW_EXTRA)


#####################
#
# Coeffects, i.e. from the outside world
#
#####################
def coeffects(world):
    return pipe(world)


#####################
#
# Business Logic
#
#####################
def discover_account_types(world):
    output = {
        'isAudit': True,
        'isConnectable': True,
        'isCloudTrailOwner': True,
        'isMasterPayer': True,
    }
    return assoc_in(world, ['output'], output)


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
