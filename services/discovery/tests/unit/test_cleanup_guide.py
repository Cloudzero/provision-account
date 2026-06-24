# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

from collections import namedtuple

import pytest
from botocore.exceptions import ClientError

import src.cleanup_guide as cg
from src import cfnresponse

BUCKET = 'cz-cur-hourly-csv-abc123'


def make_event(request_type='Create', bucket=BUCKET, legacy='old-stack-1,old-stack-2'):
    return {
        'RequestType': request_type,
        'PhysicalResourceId': None,
        'RequestId': 'req',
        'LogicalResourceId': 'logical',
        'StackId': 'stack',
        'ResponseURL': 'https://cfn.amazonaws.com/cb',
        'ResourceProperties': {
            'BucketName': bucket,
            'DetectedLegacyConnectionStacks': legacy,
        },
    }


@pytest.fixture()
def context(mocker):
    ctx = namedtuple('ctx', ['send', 'put_client', 'base_s3'])
    ctx.send = mocker.patch('src.cleanup_guide.cfnresponse.send', autospec=True)
    ctx.base_s3 = mocker.patch('src.cleanup_guide.s3')
    ctx.base_s3.get_bucket_location.return_value = {'LocationConstraint': 'us-west-2'}
    ctx.put_client = mocker.MagicMock()
    mocker.patch('src.cleanup_guide.boto3.client', return_value=ctx.put_client)
    yield ctx
    mocker.stopall()


def _assert_success(context):
    assert context.send.call_count == 1
    ((_, _, status, _, _), _) = context.send.call_args
    assert status == cfnresponse.SUCCESS


@pytest.mark.unit
def test_writes_guide_on_create_with_legacy_and_bucket(context):
    cg.handler(make_event(), None)
    _assert_success(context)
    context.put_client.put_object.assert_called_once()
    _, kwargs = context.put_client.put_object.call_args
    assert kwargs['Bucket'] == BUCKET
    assert kwargs['Key'] == cg.GUIDE_KEY
    body = kwargs['Body'].decode('utf-8')
    assert 'old-stack-1' in body and 'old-stack-2' in body


@pytest.mark.unit
def test_skips_when_no_legacy_stacks(context):
    cg.handler(make_event(legacy=''), None)
    _assert_success(context)
    context.put_client.put_object.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize('bucket', ['null', '', None])
def test_skips_when_no_bucket(context, bucket):
    cg.handler(make_event(bucket=bucket), None)
    _assert_success(context)
    context.put_client.put_object.assert_not_called()


@pytest.mark.unit
def test_noop_on_delete(context):
    cg.handler(make_event(request_type='Delete'), None)
    _assert_success(context)
    context.put_client.put_object.assert_not_called()


@pytest.mark.unit
def test_put_failure_is_swallowed(context):
    context.put_client.put_object.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'no'}}, 'PutObject')
    cg.handler(make_event(), None)
    # Best-effort: a failed write must still succeed the custom resource.
    _assert_success(context)


@pytest.mark.unit
def test_build_guide_lists_stacks():
    guide = cg.build_guide(['stack-a', 'stack-b'])
    assert '- `stack-a`' in guide
    assert '- `stack-b`' in guide
    assert 'CloudZero connection cleanup' in guide
