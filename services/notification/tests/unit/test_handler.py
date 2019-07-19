# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import os

import attrdict
import cfnresponse
import pytest
from voluptuous import All, Schema, ALLOW_EXTRA
from toolz.curried import assoc_in

import src.app as app

# TODO: Replace these fixtures with Voluptuous Schemas + Hypothesis + Property Tests
@pytest.fixture()
def cfn_event():
    return {
        'LogicalResourceId': 'some logical resource id',
        'PhysicalResourceId': None,
        'RequestId': 'some request id',
        'RequestType': 'Create',
        'ResourceProperties': {
        },
        'ResponseURL': 'https://cfn.amazonaws.com/callback',
        'StackId': 'some-cfn-stack-id',
    }


@pytest.fixture(scope='function')
def context(mocker):
    context = attrdict.AttrMap()
    orig_env = os.environ.copy()
    context.os = {'environ': os.environ}
    context.prefix = app.__name__
    context.mock_cfnresponse_send = mocker.patch(f'{context.prefix}.cfnresponse.send', autospec=True)
    context.mock_ct = mocker.patch(f'{context.prefix}.sqs', autospec=True)
    yield context
    os.environ = orig_env
    mocker.stopall()


@pytest.mark.unit
def test_handler(context, cfn_event):
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == app.DEFAULT_OUTPUT
