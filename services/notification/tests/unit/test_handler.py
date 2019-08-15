# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import os

import attrdict
import cfnresponse
import pytest
import simplejson as json
# from voluptuous import All, Schema, ALLOW_EXTRA
# from toolz.curried import assoc_in

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
            'AccountId': 'str',
            'Region': 'str',
            'ExternalId': 'str',
            'ReactorCallbackUrl': 'str',
            'AccountName': 'str',
            'ReactorId': 'str',
            'Stacks': {
                'AuditAccount': 'stack-arn',
                'CloudTrailOwnerAccount': 'stack-arn',
                'Discovery': 'stack-arn',
                'MasterPayerAccount': 'stack-arn',
                'ResourceOwnerAccount': 'stack-arn',
                'LegacyAccount': 'stack-arn',
            }
        },
        'ResponseURL': 'https://cfn.amazonaws.com/callback',
        'StackId': 'some-cfn-stack-id',
    }


class Response:
    def __init__(self, status_code, json_data={}, data={}):
        self.status_code = status_code
        self.json = json_data
        self.data = {}
        self.text = json.dumps(self.json)

    def json(self):
        return self.json

    def data(self):
        return self.data


@pytest.fixture(scope='function')
def context(mocker):
    context = attrdict.AttrMap()
    orig_env = os.environ.copy()
    context.os = {'environ': os.environ}
    context.prefix = app.__name__
    context.mock_cfnresponse_send = mocker.patch(f'{context.prefix}.cfnresponse.send', autospec=True)
    context.mock_requests_post = mocker.patch(f'{context.prefix}.requests.post', autospec=True)
    context.mock_cfn = mocker.patch(f'{context.prefix}.cfn', autospec=True)
    yield context
    os.environ = orig_env
    mocker.stopall()


@pytest.mark.unit
def test_handler_no_cfn_coeffects(context, cfn_event):
    response = Response(200)
    context.mock_requests_post.return_value = response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    assert context.mock_requests_post.call_count == 1
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
                'is_resource_owner_account': False,
                'master_payer_billing_bucket_name': None,
                'master_payer_billing_bucket_path': None,
                'remote_cloudtrail_bucket': True,
            },
            'metadata': {
                'cloud_region': 'str',
                'cz_account_name': 'str',
                'cloud_account_id': 'str',
                'reactor_callback_url': 'str',
                'external_id': 'str',
                'reactor_id': 'str',
            },
            'links': {
                'audit': {'role_arn': None},
                'legacy': {'role_arn': None},
                'master_payer': {'role_arn': None},
                'resource_owner': {'role_arn': None},
                'cloudtrail_owner': {
                    'sqs_queue_arn': None,
                    'sqs_queue_policy_name': None,
                },
            }
        }
    }
    assert status == cfnresponse.SUCCESS
    assert output == expected
    (_, kwargs) = context.mock_requests_post.call_args
    assert 'json' in kwargs
    assert kwargs['json'] == expected
