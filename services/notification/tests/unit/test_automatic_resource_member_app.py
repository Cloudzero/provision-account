# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import os
import json
from collections import namedtuple

import pytest

import src.automatic_resource_member_app as app
from src import cfnresponse


EXPECTED_URL = 'url'


class Response:
    def __init__(self, status, data=''):
        self.status = status
        self.data = data.encode('utf-8')


@pytest.fixture(scope='function')
def cfn_event():
    return {
        'LogicalResourceId': 'some logical resource id',
        'PhysicalResourceId': None,
        'RequestId': 'some request id',
        'RequestType': 'Create',
        'ResourceProperties': {
            'AccountId': 'str',
            'Region': 'str',
            'ExternalId': 'str',
            'ReactorCallbackUrl': EXPECTED_URL,
            'AccountName': 'str',
            'ReactorId': 'str',
            'ResourceOwnerRoleArn': 'arn:aws:iam::123456789012:role/CloudZeroResourceOwnerRole'
        },
        'ResponseURL': 'https://cfn.amazonaws.com/callback',
        'StackId': 'some-cfn-stack-id',
    }


@pytest.fixture(scope='function')
def context(mocker):
    context = namedtuple('context', ['os', 'prefix', 'mock_cfnresponse_send', 'mock_http', 'mock_logger'])
    orig_env = os.environ.copy()
    context.os = {'environ': os.environ}
    context.prefix = app.__name__
    context.mock_cfnresponse_send = mocker.patch(f'{context.prefix}.cfnresponse.send', autospec=True)
    context.mock_http = mocker.patch(f'{context.prefix}.http')
    context.mock_logger = mocker.patch(f'{context.prefix}.logger')
    yield context
    os.environ = orig_env
    mocker.stopall()


@pytest.mark.unit
def test_handler_create(context, cfn_event):
    response = Response(200)
    context.mock_http.request.return_value = response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    assert context.mock_http.request.call_count == 1
    ((_, _, status, output, _), _) = context.mock_cfnresponse_send.call_args
    expected = {
        'version': '1',
        'message_source': 'cfn',
        'message_type': 'account-link-provisioned',
        'data': {
            'discovery': {
                'audit_cloudtrail_bucket_name': None,
                'audit_cloudtrail_bucket_prefix': None,
                'cloudtrail_sns_topic_arn': None,
                'cloudtrail_trail_arn': None,
                'is_audit_account': False,
                'is_cloudtrail_owner_account': False,
                'is_master_payer_account': False,
                'is_organization_trail': False,
                'is_organization_master_account': False,
                'is_resource_owner_account': True,
                'master_payer_billing_bucket_name': None,
                'master_payer_billing_bucket_path': None,
                'remote_cloudtrail_bucket': False,
                'visible_cloudtrail_arns': None,
            },
            'metadata': {
                'cloud_region': 'str',
                'cz_account_name': 'str',
                'cloud_account_id': 'str',
                'reactor_callback_url': EXPECTED_URL,
                'external_id': 'str',
                'reactor_id': 'str',
            },
            'links': {
                'audit': {'role_arn': None},
                'legacy': {'role_arn': 'arn:aws:iam::123456789012:role/CloudZeroResourceOwnerRole'},
                'master_payer': {'role_arn': None},
                'resource_owner': {'role_arn': 'arn:aws:iam::123456789012:role/CloudZeroResourceOwnerRole'},
                'cloudtrail_owner': {
                    'sqs_queue_arn': None,
                    'sqs_queue_policy_name': None,
                },
            }
        }
    }
    assert status == cfnresponse.SUCCESS
    assert output == expected
    (args, kwargs) = context.mock_http.request.call_args
    assert args == ('POST', EXPECTED_URL)
    assert json.loads(kwargs['body']) == expected


@pytest.mark.unit
def test_handler_delete(context, cfn_event):
    cfn_event['RequestType'] = 'Delete'
    response = Response(200)
    context.mock_http.request.return_value = response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), _) = context.mock_cfnresponse_send.call_args
    assert output['message_type'] == 'account-link-deprovisioned'


@pytest.mark.unit
def test_handler_http_failure(context, cfn_event):
    response = Response(500)
    context.mock_http.request.return_value = response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    assert context.mock_http.request.call_count == 1


@pytest.mark.unit
def test_prepare_output(context, cfn_event):
    world = {'event': cfn_event}
    new_world = app.prepare_output(world)
    output = new_world['output']
    assert output['data']['links']['resource_owner']['role_arn'] == 'arn:aws:iam::123456789012:role/CloudZeroResourceOwnerRole'
    assert output['data']['links']['legacy']['role_arn'] == 'arn:aws:iam::123456789012:role/CloudZeroResourceOwnerRole'
    assert output['data']['discovery']['is_resource_owner_account'] is True


@pytest.mark.unit
def test_handler_exception(context, cfn_event, mocker):
    # Mock prepare_output to raise an exception
    mocker.patch(f'{context.prefix}.prepare_output', side_effect=Exception('Test exception'))
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), _) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output is None


@pytest.mark.unit
def test_handler_with_kwargs(context, cfn_event):
    response = Response(200)
    context.mock_http.request.return_value = response
    kwargs = {'test_param': 'test_value'}
    ret = app.handler(cfn_event, None, **kwargs)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1


@pytest.mark.unit
def test_effects_reactor_callback_exception(context, cfn_event):
    context.mock_http.request.side_effect = Exception('HTTP request failed')
    world = {
        'event': cfn_event,
        'output': {
            'version': '1',
            'message_source': 'cfn',
            'message_type': 'account-link-provisioned',
            'data': {}
        }
    }
    result = app.effects_reactor_callback(world)
    assert 'effects' in result
    assert 'reactor' in result['effects']
    assert result['effects']['reactor'] == {}


@pytest.mark.unit
def test_handler_update_request(context, cfn_event):
    cfn_event['RequestType'] = 'Update'
    response = Response(200)
    context.mock_http.request.return_value = response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), _) = context.mock_cfnresponse_send.call_args
    assert output['message_type'] == 'account-link-provisioned'


@pytest.mark.unit
def test_handler_with_physical_resource_id(context, cfn_event):
    cfn_event['PhysicalResourceId'] = 'existing-resource-id'
    response = Response(200)
    context.mock_http.request.return_value = response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((event, _, _, _, physical_id), _) = context.mock_cfnresponse_send.call_args
    assert physical_id == 'existing-resource-id'


@pytest.mark.unit
def test_input_schema_validation_failure(context, cfn_event):
    del cfn_event['ResourceProperties']['AccountId']
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), _) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output is None


@pytest.mark.unit
def test_notify_cloudzero_flow(context, cfn_event):
    world = {'event': cfn_event}
    result = app.notify_cloudzero(world)
    assert 'output' in result
    assert result['output']['message_type'] == 'account-link-provisioned'
    assert result['output']['data']['metadata']['cloud_account_id'] == 'str'


@pytest.mark.unit
def test_effect_decorator(context):
    @app.effect('test_effect')
    def test_function(world):
        return {'result': 'success'}

    world = {}
    result = test_function(world)
    assert 'effects' in result
    assert 'test_effect' in result['effects']
    assert result['effects']['test_effect'] == {'result': 'success'}


@pytest.mark.unit
def test_effect_decorator_with_exception(context):
    @app.effect('test_effect')
    def test_function(world):
        raise Exception('Test exception')

    world = {}
    result = test_function(world)
    assert 'effects' in result
    assert 'test_effect' in result['effects']
    assert result['effects']['test_effect'] == {}
