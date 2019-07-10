# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import os

import attrdict
import cfnresponse
import pytest

import src.app as app


LOCAL_ACCOUNT_ID = '123456789012'
REMOTE_ACCOUNT_ID = '999999999999'

LOCAL_BUCKET_NAME = 'local-bucket'
REMOTE_BUCKET_NAME = 'remote-bucket'

LOCAL_TRAIL_ARN = f'arn:aws:cloudtrail:us-east-1:{LOCAL_ACCOUNT_ID}:trail/local-trail'
REMOTE_TRAIL_ARN = f'arn:aws:cloudtrail:us-east-1:{REMOTE_ACCOUNT_ID}:trail/remote-trail'

LOCAL_TOPIC_ARN = f'arn:aws:sns:us-east-1:{LOCAL_ACCOUNT_ID}:local-cloudtrail-topic'
REMOTE_TOPIC_ARN = f'arn:aws:sns:us-east-1:{REMOTE_ACCOUNT_ID}:remote-cloudtrail-topic'


@pytest.fixture()
def cfn_event():
    return {
        'ResourceProperties': {
            'accountId': LOCAL_ACCOUNT_ID,
        },
        'PhysicalResourceId': None,
    }


@pytest.fixture()
def describe_trails_response():
    return {
        'trailList': [
            {
                'HasCustomEventSelectors': True,
                'HomeRegion': 'us-east-1',
                'IncludeGlobalServiceEvents': True,
                'IsMultiRegionTrail': True,
                'IsOrganizationTrail': False,
                'LogFileValidationEnabled': True,
                'Name': 'my-local-trail',
                'S3BucketName': LOCAL_BUCKET_NAME,
                'SnsTopicARN': LOCAL_TOPIC_ARN,
                'SnsTopicName': LOCAL_TOPIC_ARN,
                'TrailARN': LOCAL_TRAIL_ARN,
            },
        ],
    }


@pytest.fixture()
def list_buckets_response():
    return {
        'Buckets': [
            {
                'Name': LOCAL_BUCKET_NAME,
            }
        ]
    }


@pytest.fixture()
def describe_report_definitions_response():
    return {
        'ReportDefinitions': [
            {
                'S3Bucket': LOCAL_BUCKET_NAME,
                'S3Prefix': 'path',
                'ReportName': 'billing_report',
            }
        ]
    }


@pytest.fixture(scope='function')
def context(mocker):
    context = attrdict.AttrMap()
    orig_env = os.environ.copy()
    context.os = {'environ': os.environ}
    context.prefix = app.__name__
    context.mock_cfnresponse_send = mocker.patch(f'{context.prefix}.cfnresponse.send', autospec=True)
    context.mock_ct = mocker.patch(f'{context.prefix}.ct', autospec=True)
    context.mock_cur = mocker.patch(f'{context.prefix}.cur', autospec=True)
    context.mock_s3 = mocker.patch(f'{context.prefix}.s3', autospec=True)
    yield context
    os.environ = orig_env
    mocker.stopall()


@pytest.mark.unit
def test_handler(context, cfn_event, describe_trails_response, list_buckets_response, describe_report_definitions_response):
    context.mock_ct.describe_trails.return_value = describe_trails_response
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response
    context.mock_s3.list_buckets.return_value = list_buckets_response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    app.OUTPUT_SCHEMA({'output': output})
