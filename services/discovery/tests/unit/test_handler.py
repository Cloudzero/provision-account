# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import cfnresponse
import pytest

import src.app as app


@pytest.fixture()
def cfn_event():
    return {
        'ResourceProperties': {},
        'PhysicalResourceId': None,
    }


@pytest.mark.unit
def test_handler(cfn_event, mocker):
    cfnresponse = mocker.patch(f'{app.__name__}.cfnresponse', autospec=True)
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert cfnresponse.send.call_count == 1
    ((_, _, status, output, _), kwargs) = cfnresponse.send.call_args
    assert status == cfnresponse.SUCCESS
    app.OUTPUT_SCHEMA({'output': output})
