# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import os
import json
from collections import namedtuple

import pytest

import src.app as app
from src import cfnresponse

EXPECTED_URL = 'https://api.cloudzero.com/accounts/v1/link'
ACCOUNT_ID = '123456789012'
CONNECTION_ROLE_ARN = f'arn:aws:iam::{ACCOUNT_ID}:role/cloudzero/cloudzero-connection'

# The fixed reactor-payload key set. These tests guard it against accidental drift.
EXPECTED_LINK_KEYS = {'audit', 'cloudtrail_owner', 'master_payer', 'resource_owner', 'legacy'}
EXPECTED_DISCOVERY_KEYS = {
    'audit_cloudtrail_bucket_name', 'audit_cloudtrail_bucket_prefix', 'cloudtrail_sns_topic_arn',
    'cloudtrail_trail_arn', 'is_audit_account', 'is_cloudtrail_owner_account', 'is_organization_trail',
    'remote_cloudtrail_bucket', 'visible_cloudtrail_arns', 'is_master_payer_account',
    'is_organization_master_account', 'is_resource_owner_account', 'master_payer_billing_bucket_name',
    'master_payer_billing_bucket_path',
}


def make_event(request_type='Create', **overrides):
    properties = {
        'AccountId': ACCOUNT_ID,
        'Region': 'us-east-1',
        'ExternalId': 'ext-id',
        'ReactorCallbackUrl': EXPECTED_URL,
        'AccountName': 'my-account',
        'ReactorId': 'reactor-1',
        'IsResourceConnection': 'true',
        'IsBillingConnection': 'false',
        'IsOrganizationMasterAccount': 'false',
        'ConnectionRoleArn': 'null',
        'BillingBucketName': 'null',
        'BillingBucketPath': 'null',
        'BillingReportS3Bucket': 'null',
        'BillingReportS3Prefix': 'null',
        'BillingReportFormat': 'null',
    }
    properties.update(overrides)
    return {
        'LogicalResourceId': 'some logical resource id',
        'PhysicalResourceId': None,
        'RequestId': 'some request id',
        'RequestType': request_type,
        'ResourceProperties': properties,
        'ResponseURL': 'https://cfn.amazonaws.com/callback',
        'StackId': 'some-cfn-stack-id',
    }


class FakeResponse:
    def __init__(self, status=200, body=b'ok'):
        self.status = status
        self.data = body


@pytest.fixture(scope='function')
def context(mocker):
    context = namedtuple('context', ['os', 'prefix'])
    orig_env = os.environ.copy()
    context.os = {'environ': os.environ}
    context.prefix = app.__name__
    context.mock_cfnresponse_send = mocker.patch(f'{context.prefix}.cfnresponse.send', autospec=True)
    context.mock_http = mocker.patch(f'{context.prefix}.http')
    context.mock_http.request.return_value = FakeResponse()
    yield context
    os.environ = orig_env
    mocker.stopall()


def _sent_output(context):
    ((_, _, status, output, _), _) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    return output


@pytest.mark.unit
def test_handler_posts_fixed_contract_payload_for_billing_connection(context):
    event = make_event(
        IsBillingConnection='true',
        IsOrganizationMasterAccount='true',
        ConnectionRoleArn=CONNECTION_ROLE_ARN,
        BillingBucketName='cur-bucket',
        BillingBucketPath='cloudzero/report',
        BillingReportFormat='aws',
    )
    app.handler(event, None)
    expected = {
        'version': '1',
        'message_source': 'cfn',
        'message_type': 'account-link-provisioned',
        'data': {
            'metadata': {
                'cloud_region': 'us-east-1',
                'external_id': 'ext-id',
                'cloud_account_id': ACCOUNT_ID,
                'cz_account_name': 'my-account',
                'reactor_id': 'reactor-1',
                'reactor_callback_url': EXPECTED_URL,
                'billing_report_format': 'aws',
            },
            'links': {
                'audit': {'role_arn': None},
                'cloudtrail_owner': {'sqs_queue_arn': None, 'sqs_queue_policy_name': None},
                # The single connection role ARN is reported into all three slots.
                'master_payer': {'role_arn': CONNECTION_ROLE_ARN},
                'resource_owner': {'role_arn': CONNECTION_ROLE_ARN},
                'legacy': {'role_arn': CONNECTION_ROLE_ARN},
            },
            'discovery': {
                'audit_cloudtrail_bucket_name': None,
                'audit_cloudtrail_bucket_prefix': None,
                'cloudtrail_sns_topic_arn': None,
                'cloudtrail_trail_arn': None,
                'is_audit_account': False,
                'is_cloudtrail_owner_account': False,
                'is_organization_trail': None,
                'remote_cloudtrail_bucket': True,
                'visible_cloudtrail_arns': None,
                'is_master_payer_account': True,
                'is_organization_master_account': True,
                'is_resource_owner_account': True,
                'master_payer_billing_bucket_name': 'cur-bucket',
                'master_payer_billing_bucket_path': 'cloudzero/report',
            },
        },
    }
    assert _sent_output(context) == expected
    (args, kwargs) = context.mock_http.request.call_args
    assert args == ('POST', EXPECTED_URL)
    assert json.loads(kwargs['body']) == expected


@pytest.mark.unit
def test_handler_payload_key_set_is_unchanged(context):
    app.handler(make_event(), None)
    data = _sent_output(context)['data']
    assert set(data['links']) == EXPECTED_LINK_KEYS
    assert set(data['discovery']) == EXPECTED_DISCOVERY_KEYS


@pytest.mark.unit
def test_handler_billing_connection_reports_one_arn_in_all_slots(context):
    event = make_event(IsBillingConnection='true', ConnectionRoleArn=CONNECTION_ROLE_ARN)
    app.handler(event, None)
    links = _sent_output(context)['data']['links']
    assert links['master_payer']['role_arn'] == CONNECTION_ROLE_ARN
    assert links['resource_owner']['role_arn'] == CONNECTION_ROLE_ARN
    assert links['legacy']['role_arn'] == CONNECTION_ROLE_ARN


@pytest.mark.unit
def test_handler_resource_only_connection_has_null_master_payer(context):
    # Resource-only (non-billing) connection: resource/legacy carry the ARN, master_payer is null.
    event = make_event(IsBillingConnection='false', ConnectionRoleArn=CONNECTION_ROLE_ARN)
    app.handler(event, None)
    links = _sent_output(context)['data']['links']
    assert links['resource_owner']['role_arn'] == CONNECTION_ROLE_ARN
    assert links['legacy']['role_arn'] == CONNECTION_ROLE_ARN
    assert links['master_payer']['role_arn'] is None
    assert _sent_output(context)['data']['discovery']['is_master_payer_account'] is False


@pytest.mark.unit
def test_handler_deprecated_audit_cloudtrail_fields_are_null(context):
    app.handler(make_event(), None)
    data = _sent_output(context)['data']
    assert data['links']['audit'] == {'role_arn': None}
    assert data['links']['cloudtrail_owner'] == {'sqs_queue_arn': None, 'sqs_queue_policy_name': None}
    assert data['discovery']['is_audit_account'] is False
    assert data['discovery']['is_cloudtrail_owner_account'] is False
    assert data['discovery']['cloudtrail_sns_topic_arn'] is None
    assert data['discovery']['audit_cloudtrail_bucket_name'] is None


@pytest.mark.unit
@pytest.mark.parametrize('raw_format,expected', [
    ('aws_parquet', 'aws_parquet'),
    ('null', 'aws'),
    ('aws', 'aws'),
])
def test_handler_billing_format_fallback(context, raw_format, expected):
    app.handler(make_event(BillingReportFormat=raw_format), None)
    assert _sent_output(context)['data']['metadata']['billing_report_format'] == expected


@pytest.mark.unit
def test_handler_billing_bucket_falls_back_to_created_report(context):
    # No existing discovered bucket, but a CUR was freshly created -> use the report outputs.
    event = make_event(
        IsBillingConnection='true',
        ConnectionRoleArn=CONNECTION_ROLE_ARN,
        BillingBucketName='null',
        BillingBucketPath='null',
        BillingReportS3Bucket='new-cur-bucket',
        BillingReportS3Prefix='cloudzero/cloudzero-cur-hourly-csv',
    )
    app.handler(event, None)
    discovery = _sent_output(context)['data']['discovery']
    assert discovery['master_payer_billing_bucket_name'] == 'new-cur-bucket'
    assert discovery['master_payer_billing_bucket_path'] == 'cloudzero/cloudzero-cur-hourly-csv'


@pytest.mark.unit
def test_handler_delete_sends_deprovisioned(context):
    app.handler(make_event(request_type='Delete'), None)
    assert _sent_output(context)['message_type'] == 'account-link-deprovisioned'


@pytest.mark.unit
def test_handler_posts_once_and_responds_success(context):
    app.handler(make_event(), None)
    assert context.mock_http.request.call_count == 1
    assert context.mock_cfnresponse_send.call_count == 1


# ---- cfnresponse (vendored AWS helper that ships in the Lambda) ----

CfnContext = namedtuple('CfnContext', ['log_stream_name'])

CFN_RESPONSE_EVENT = {
    'ResponseURL': 'https://cfn.amazonaws.com/presigned',
    'StackId': 'stack-id',
    'RequestId': 'request-id',
    'LogicalResourceId': 'logical-id',
}


@pytest.mark.unit
def test_cfnresponse_send_puts_response_body(mocker):
    mock_http = mocker.patch(f'{cfnresponse.__name__}.http')
    mock_http.request.return_value = FakeResponse()
    mock_http.request.return_value.reason = 'OK'
    cfnresponse.send(CFN_RESPONSE_EVENT, CfnContext('log-stream'), cfnresponse.SUCCESS, {'k': 'v'})
    (args, kwargs) = mock_http.request.call_args
    assert args[0] == 'PUT'
    assert args[1] == CFN_RESPONSE_EVENT['ResponseURL']
    body = json.loads(kwargs['body'])
    assert body['Status'] == cfnresponse.SUCCESS
    assert body['PhysicalResourceId'] == 'log-stream'  # falls back to log_stream_name
    assert body['Data'] == {'k': 'v'}


@pytest.mark.unit
def test_cfnresponse_send_swallows_http_errors(mocker):
    mock_http = mocker.patch(f'{cfnresponse.__name__}.http')
    mock_http.request.side_effect = Exception('network down')
    # Must not raise -- a failed callback should never fail the custom resource.
    cfnresponse.send(CFN_RESPONSE_EVENT, CfnContext('log-stream'), cfnresponse.FAILED, {}, physicalResourceId='pid')
