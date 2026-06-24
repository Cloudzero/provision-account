# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import os
from collections import namedtuple

import pytest
from botocore.exceptions import ClientError

import src.app as app
from src import cfnresponse


LOCAL_ACCOUNT_ID = '123456789012'
REMOTE_ACCOUNT_ID = '999999999999'

LOCAL_BUCKET_NAME = 'local-bucket'
SECOND_LOCAL_BUCKET_NAME = 'another-local-cur-bucket'
REMOTE_BUCKET_NAME = 'remote-bucket'
DATA_EXPORT_BUCKET_NAME = 'cur2-data-export-bucket'

CURRENT_STACK_ID = 'some-cfn-stack-id'
EXPORT_ARN = f'arn:aws:bcm-data-exports:us-east-1:{LOCAL_ACCOUNT_ID}:export/cur2-export'


@pytest.fixture()
def cfn_event():
    return {
        'LogicalResourceId': 'some logical resource id',
        'PhysicalResourceId': None,
        'RequestId': 'some request id',
        'RequestType': 'Create',
        'ResourceProperties': {
            'AccountId': LOCAL_ACCOUNT_ID,
        },
        'ResponseURL': 'https://cfn.amazonaws.com/callback',
        'StackId': CURRENT_STACK_ID,
    }


@pytest.fixture()
def describe_organizations_local():
    return {'Organization': {'MasterAccountId': LOCAL_ACCOUNT_ID}}


@pytest.fixture()
def describe_organizations_remote():
    return {'Organization': {'MasterAccountId': REMOTE_ACCOUNT_ID}}


@pytest.fixture()
def describe_organizations_not_in_organization_error():
    return ClientError({'Error': {'Code': 'AWSOrganizationsNotInUseException',
                                  'Message': 'Your account is not a member of an organization'}},
                       'DescribeOrganization')


@pytest.fixture()
def list_buckets_response():
    return {'Buckets': [{'Name': LOCAL_BUCKET_NAME}]}


@pytest.fixture()
def describe_report_definitions_response_local():
    return {
        'ReportDefinitions': [
            {
                'S3Bucket': LOCAL_BUCKET_NAME,
                'S3Prefix': 'path',
                'ReportName': 'billing_report',
            },
            {
                'ReportName': 'valid-local-report',
                'TimeUnit': 'HOURLY',
                'Format': 'textORcsv',
                'Compression': 'GZIP',
                'AdditionalSchemaElements': ['RESOURCES'],
                'S3Bucket': LOCAL_BUCKET_NAME,
                'S3Prefix': 'reports',
                'S3Region': 'us-east-1',
                'AdditionalArtifacts': ['REDSHIFT'],
                'RefreshClosedReports': True,
                'ReportVersioning': 'CREATE_NEW_REPORT',
            },
        ]
    }


@pytest.fixture()
def describe_report_definitions_response_remote():
    return {
        'ReportDefinitions': [
            {
                'ReportName': 'valid-local-report',
                'TimeUnit': 'HOURLY',
                'Format': 'textORcsv',
                'Compression': 'GZIP',
                'AdditionalSchemaElements': ['RESOURCES'],
                'S3Bucket': REMOTE_BUCKET_NAME,
                'S3Prefix': 'reports',
                'S3Region': 'us-east-1',
                'AdditionalArtifacts': ['REDSHIFT'],
                'RefreshClosedReports': True,
                'ReportVersioning': 'CREATE_NEW_REPORT',
            }
        ]
    }


PARQUET_REPORT = {
    'ReportName': 'valid-parquet-report',
    'TimeUnit': 'HOURLY',
    'Format': 'Parquet',
    'Compression': 'Parquet',
    'AdditionalSchemaElements': ['RESOURCES'],
    'S3Bucket': LOCAL_BUCKET_NAME,
    'S3Prefix': 'reports',
    'S3Region': 'us-east-1',
    'RefreshClosedReports': True,
    'ReportVersioning': 'CREATE_NEW_REPORT',
}

CSV_REPORT = {
    'ReportName': 'valid-csv-report',
    'TimeUnit': 'HOURLY',
    'Format': 'textORcsv',
    'Compression': 'GZIP',
    'AdditionalSchemaElements': ['RESOURCES'],
    'S3Bucket': LOCAL_BUCKET_NAME,
    'S3Prefix': 'reports',
    'S3Region': 'us-east-1',
    'RefreshClosedReports': True,
    'ReportVersioning': 'CREATE_NEW_REPORT',
}

MINIMUM_CSV_REPORT = {
    'ReportName': 'minimum-csv-report',
    'TimeUnit': 'HOURLY',
    'Format': 'textORcsv',
    'Compression': 'GZIP',
    'S3Bucket': LOCAL_BUCKET_NAME,
    'S3Prefix': 'reports',
    'S3Region': 'us-east-1',
    'RefreshClosedReports': True,
}


@pytest.fixture()
def describe_report_definitions_response_invalid():
    return {
        'ReportDefinitions': [
            {
                'S3Bucket': LOCAL_BUCKET_NAME,
                'S3Prefix': 'path',
                'ReportName': 'billing_report',
            },
        ]
    }


@pytest.fixture()
def describe_report_definitions_client_error():
    return ClientError({'Error': {'Code': 'AccessDeniedException',
                                  'Message': 'is not authorized to call DescribeReportDefinitions'}},
                       'DescribeReportDefinitions')


@pytest.fixture(scope='function')
def context(mocker):
    context = namedtuple('context', ['os', 'prefix'])
    orig_env = os.environ.copy()
    context.os = {'environ': os.environ}
    context.prefix = app.__name__
    context.mock_cfnresponse_send = mocker.patch(f'{context.prefix}.cfnresponse.send', autospec=True)
    context.mock_cur = mocker.patch(f'{context.prefix}.cur', autospec=True)
    context.mock_bcm = mocker.patch(f'{context.prefix}.bcm', autospec=True)
    context.mock_bcm.list_exports.return_value = {'Exports': []}
    context.mock_orgs = mocker.patch(f'{context.prefix}.orgs', autospec=True)
    context.mock_s3 = mocker.patch(f'{context.prefix}.s3', autospec=True)
    context.mock_cf = mocker.patch(f'{context.prefix}.cf', autospec=True)
    context.mock_cf.describe_stacks.return_value = {'Stacks': []}
    yield context
    os.environ = orig_env
    mocker.stopall()


def _output(context):
    ((_, _, status, output, _), _) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    return output


@pytest.mark.unit
def test_handler_billing_org_master_with_local_cur(
    context, cfn_event, list_buckets_response,
    describe_report_definitions_response_local, describe_organizations_local,
):
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = list_buckets_response
    app.handler(cfn_event, None)
    assert _output(context) == {
        'IsResourceConnection': True,
        'IsBillingConnection': True,
        'IsOrganizationMasterAccount': True,
        'IsAccountOutsideOrganization': False,
        'BillingBucketName': LOCAL_BUCKET_NAME,
        'BillingBucketPath': 'reports/valid-local-report',
        'BillingBucketArns': f'arn:aws:s3:::{LOCAL_BUCKET_NAME},arn:aws:s3:::{LOCAL_BUCKET_NAME}/*',
        'BillingReportFormat': 'aws',
        'DetectedLegacyConnectionStacks': '',
    }


@pytest.mark.unit
def test_handler_billing_outside_organization(
    context, cfn_event, list_buckets_response,
    describe_report_definitions_response_invalid, describe_organizations_not_in_organization_error,
):
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_invalid
    context.mock_orgs.describe_organization.side_effect = describe_organizations_not_in_organization_error
    context.mock_s3.list_buckets.return_value = list_buckets_response
    app.handler(cfn_event, None)
    output = _output(context)
    assert output['IsBillingConnection'] is True
    assert output['IsAccountOutsideOrganization'] is True
    assert output['IsOrganizationMasterAccount'] is False
    # No valid ingestable CUR, but the bucket the invalid report references is still granted.
    assert output['BillingBucketName'] is None
    assert output['BillingBucketArns'] == (
        f'arn:aws:s3:::{LOCAL_BUCKET_NAME},arn:aws:s3:::{LOCAL_BUCKET_NAME}/*'
    )


@pytest.mark.unit
def test_handler_not_billing_when_org_master_is_remote(
    context, cfn_event, list_buckets_response,
    describe_report_definitions_response_remote, describe_organizations_remote,
):
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_remote
    context.mock_orgs.describe_organization.return_value = describe_organizations_remote
    context.mock_s3.list_buckets.return_value = list_buckets_response
    app.handler(cfn_event, None)
    output = _output(context)
    assert output['IsBillingConnection'] is False
    assert output['IsOrganizationMasterAccount'] is False
    assert output['BillingBucketName'] is None
    assert output['BillingBucketArns'] == ''


@pytest.mark.unit
def test_handler_only_resource_connection_when_cur_access_denied(
    context, cfn_event, describe_report_definitions_client_error, describe_organizations_remote,
):
    context.mock_cur.describe_report_definitions.side_effect = describe_report_definitions_client_error
    context.mock_orgs.describe_organization.return_value = describe_organizations_remote
    context.mock_s3.list_buckets.return_value = {'Buckets': []}
    app.handler(cfn_event, None)
    assert _output(context) == {**app.DEFAULT_OUTPUT, 'IsResourceConnection': True}


@pytest.mark.unit
def test_handler_exception_returns_default_output(context):
    app.handler({}, None)
    assert _output(context) == app.DEFAULT_OUTPUT


@pytest.mark.unit
@pytest.mark.parametrize('report_definitions,expected_format', [
    ({'ReportDefinitions': [PARQUET_REPORT]}, 'aws_parquet'),
    ({'ReportDefinitions': [PARQUET_REPORT, CSV_REPORT]}, 'aws'),
    ({'ReportDefinitions': [PARQUET_REPORT, MINIMUM_CSV_REPORT]}, 'aws'),  # ideal Parquet + minimum CSV → CSV wins
])
def test_handler_cur_format_detection(
    context, cfn_event, list_buckets_response, describe_organizations_local,
    report_definitions, expected_format,
):
    context.mock_cur.describe_report_definitions.return_value = report_definitions
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = list_buckets_response
    app.handler(cfn_event, None)
    output = _output(context)
    assert output['BillingReportFormat'] == expected_format
    assert output['BillingBucketName'] == LOCAL_BUCKET_NAME
    assert output['IsBillingConnection'] is True


@pytest.fixture()
def list_buckets_response_two_local():
    return {'Buckets': [{'Name': LOCAL_BUCKET_NAME}, {'Name': SECOND_LOCAL_BUCKET_NAME}]}


@pytest.mark.unit
def test_handler_enumerates_all_local_cur_buckets(
    context, cfn_event, list_buckets_response_two_local, describe_organizations_local,
):
    second_report = dict(CSV_REPORT, ReportName='second-cur', S3Bucket=SECOND_LOCAL_BUCKET_NAME, S3Prefix='cz')
    context.mock_cur.describe_report_definitions.return_value = {'ReportDefinitions': [CSV_REPORT, second_report]}
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = list_buckets_response_two_local
    app.handler(cfn_event, None)
    expected = ','.join([
        f'arn:aws:s3:::{SECOND_LOCAL_BUCKET_NAME}',
        f'arn:aws:s3:::{SECOND_LOCAL_BUCKET_NAME}/*',
        f'arn:aws:s3:::{LOCAL_BUCKET_NAME}',
        f'arn:aws:s3:::{LOCAL_BUCKET_NAME}/*',
    ])
    assert _output(context)['BillingBucketArns'] == expected


@pytest.mark.unit
def test_handler_excludes_remote_cur_buckets(
    context, cfn_event, list_buckets_response_two_local, describe_organizations_local,
):
    second_report = dict(CSV_REPORT, ReportName='second-cur', S3Bucket=SECOND_LOCAL_BUCKET_NAME, S3Prefix='cz')
    remote_report = dict(CSV_REPORT, ReportName='remote-cur', S3Bucket=REMOTE_BUCKET_NAME, S3Prefix='cz')
    context.mock_cur.describe_report_definitions.return_value = {
        'ReportDefinitions': [CSV_REPORT, second_report, remote_report]
    }
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = list_buckets_response_two_local
    app.handler(cfn_event, None)
    arns = _output(context)['BillingBucketArns']
    assert f'arn:aws:s3:::{REMOTE_BUCKET_NAME}' not in arns
    assert f'arn:aws:s3:::{SECOND_LOCAL_BUCKET_NAME}' in arns
    assert f'arn:aws:s3:::{LOCAL_BUCKET_NAME}' in arns


def _list_exports_response(*export_arns):
    return {'Exports': [{'ExportArn': arn, 'ExportName': arn.split('/')[-1]} for arn in export_arns]}


def _get_export_response(bucket_name):
    return {
        'Export': {
            'ExportArn': EXPORT_ARN,
            'Name': 'cur2-export',
            'DestinationConfigurations': {
                'S3Destination': {
                    'S3Bucket': bucket_name,
                    'S3Prefix': 'cur2',
                    'S3Region': 'us-east-1',
                    'S3OutputConfigurations': {},
                },
            },
        },
    }


@pytest.mark.unit
def test_handler_includes_local_cur2_data_export_bucket(
    context, cfn_event, describe_report_definitions_response_local, describe_organizations_local,
):
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_bcm.list_exports.return_value = _list_exports_response(EXPORT_ARN)
    context.mock_bcm.get_export.return_value = _get_export_response(DATA_EXPORT_BUCKET_NAME)
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = {
        'Buckets': [{'Name': LOCAL_BUCKET_NAME}, {'Name': DATA_EXPORT_BUCKET_NAME}]
    }
    app.handler(cfn_event, None)
    expected = ','.join([
        f'arn:aws:s3:::{DATA_EXPORT_BUCKET_NAME}',
        f'arn:aws:s3:::{DATA_EXPORT_BUCKET_NAME}/*',
        f'arn:aws:s3:::{LOCAL_BUCKET_NAME}',
        f'arn:aws:s3:::{LOCAL_BUCKET_NAME}/*',
    ])
    assert _output(context)['BillingBucketArns'] == expected
    context.mock_bcm.get_export.assert_called_once_with(ExportArn=EXPORT_ARN)


@pytest.mark.unit
def test_handler_includes_all_export_buckets_regardless_of_type(
    context, cfn_event, describe_report_definitions_response_local, describe_organizations_local,
):
    second_export_arn = f'arn:aws:bcm-data-exports:us-east-1:{LOCAL_ACCOUNT_ID}:export/focus-export'
    export_buckets = {EXPORT_ARN: DATA_EXPORT_BUCKET_NAME, second_export_arn: SECOND_LOCAL_BUCKET_NAME}
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_bcm.list_exports.return_value = _list_exports_response(EXPORT_ARN, second_export_arn)
    context.mock_bcm.get_export.side_effect = lambda ExportArn: _get_export_response(export_buckets[ExportArn])
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = {
        'Buckets': [{'Name': LOCAL_BUCKET_NAME}, {'Name': DATA_EXPORT_BUCKET_NAME}, {'Name': SECOND_LOCAL_BUCKET_NAME}]
    }
    app.handler(cfn_event, None)
    arns = _output(context)['BillingBucketArns']
    for bucket in (LOCAL_BUCKET_NAME, DATA_EXPORT_BUCKET_NAME, SECOND_LOCAL_BUCKET_NAME):
        assert f'arn:aws:s3:::{bucket}' in arns
        assert f'arn:aws:s3:::{bucket}/*' in arns


@pytest.mark.unit
def test_handler_excludes_remote_cur2_data_export_bucket(
    context, cfn_event, list_buckets_response,
    describe_report_definitions_response_local, describe_organizations_local,
):
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_bcm.list_exports.return_value = _list_exports_response(EXPORT_ARN)
    context.mock_bcm.get_export.return_value = _get_export_response(REMOTE_BUCKET_NAME)
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = list_buckets_response
    app.handler(cfn_event, None)
    arns = _output(context)['BillingBucketArns']
    assert arns == f'arn:aws:s3:::{LOCAL_BUCKET_NAME},arn:aws:s3:::{LOCAL_BUCKET_NAME}/*'
    assert f'arn:aws:s3:::{REMOTE_BUCKET_NAME}' not in arns


@pytest.mark.unit
def test_handler_survives_bcm_data_exports_access_denied(
    context, cfn_event, list_buckets_response,
    describe_report_definitions_response_local, describe_organizations_local,
):
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_bcm.list_exports.side_effect = ClientError(
        {'Error': {'Code': 'AccessDeniedException', 'Message': 'not authorized to call ListExports'}},
        'ListExports',
    )
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = list_buckets_response
    app.handler(cfn_event, None)
    assert _output(context)['BillingBucketArns'] == (
        f'arn:aws:s3:::{LOCAL_BUCKET_NAME},arn:aws:s3:::{LOCAL_BUCKET_NAME}/*'
    )


@pytest.mark.unit
def test_handler_paginates_list_exports(
    context, cfn_event, describe_report_definitions_client_error, describe_organizations_local,
):
    second_export_arn = f'arn:aws:bcm-data-exports:us-east-1:{LOCAL_ACCOUNT_ID}:export/page-two'
    export_buckets = {EXPORT_ARN: DATA_EXPORT_BUCKET_NAME, second_export_arn: SECOND_LOCAL_BUCKET_NAME}
    context.mock_cur.describe_report_definitions.side_effect = describe_report_definitions_client_error
    context.mock_bcm.list_exports.side_effect = [
        {'Exports': [{'ExportArn': EXPORT_ARN}], 'NextToken': 'page-2'},
        {'Exports': [{'ExportArn': second_export_arn}]},
    ]
    context.mock_bcm.get_export.side_effect = lambda ExportArn: _get_export_response(export_buckets[ExportArn])
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = {
        'Buckets': [{'Name': DATA_EXPORT_BUCKET_NAME}, {'Name': SECOND_LOCAL_BUCKET_NAME}]
    }
    app.handler(cfn_event, None)
    arns = _output(context)['BillingBucketArns']
    assert f'arn:aws:s3:::{DATA_EXPORT_BUCKET_NAME}' in arns
    assert f'arn:aws:s3:::{SECOND_LOCAL_BUCKET_NAME}' in arns
    assert context.mock_bcm.list_exports.call_count == 2


@pytest.mark.unit
def test_handler_skips_export_with_no_destination_bucket(
    context, cfn_event, describe_report_definitions_client_error, describe_organizations_local,
):
    # An export whose S3Destination has no S3Bucket must be silently skipped, not added
    # as an empty/None bucket.
    no_bucket_export = {'Export': {'ExportArn': EXPORT_ARN, 'Name': 'no-bucket',
                                   'DestinationConfigurations': {'S3Destination': {'S3Prefix': 'x'}}}}
    context.mock_cur.describe_report_definitions.side_effect = describe_report_definitions_client_error
    context.mock_bcm.list_exports.return_value = _list_exports_response(EXPORT_ARN)
    context.mock_bcm.get_export.return_value = no_bucket_export
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = {'Buckets': [{'Name': DATA_EXPORT_BUCKET_NAME}]}
    app.handler(cfn_event, None)
    assert _output(context)['BillingBucketArns'] == ''


@pytest.mark.unit
def test_handler_isolates_per_export_get_export_failure(
    context, cfn_event, describe_report_definitions_client_error, describe_organizations_local,
):
    bad_export_arn = f'arn:aws:bcm-data-exports:us-east-1:{LOCAL_ACCOUNT_ID}:export/broken'

    def get_export(ExportArn):
        if ExportArn == bad_export_arn:
            raise ClientError({'Error': {'Code': 'InternalFailure', 'Message': 'boom'}}, 'GetExport')
        return _get_export_response(DATA_EXPORT_BUCKET_NAME)

    context.mock_cur.describe_report_definitions.side_effect = describe_report_definitions_client_error
    context.mock_bcm.list_exports.return_value = _list_exports_response(bad_export_arn, EXPORT_ARN)
    context.mock_bcm.get_export.side_effect = get_export
    context.mock_orgs.describe_organization.return_value = describe_organizations_local
    context.mock_s3.list_buckets.return_value = {'Buckets': [{'Name': DATA_EXPORT_BUCKET_NAME}]}
    app.handler(cfn_event, None)
    # The healthy export's bucket is still granted; the failing one is skipped, not fatal.
    assert _output(context)['BillingBucketArns'] == (
        f'arn:aws:s3:::{DATA_EXPORT_BUCKET_NAME},arn:aws:s3:::{DATA_EXPORT_BUCKET_NAME}/*'
    )


@pytest.mark.unit
def test_handler_detects_legacy_connection_stacks(
    context, cfn_event, list_buckets_response,
    describe_report_definitions_client_error, describe_organizations_remote,
):
    context.mock_cur.describe_report_definitions.side_effect = describe_report_definitions_client_error
    context.mock_orgs.describe_organization.return_value = describe_organizations_remote
    context.mock_s3.list_buckets.return_value = list_buckets_response
    context.mock_cf.describe_stacks.return_value = {'Stacks': [
        # current stack (excluded by StackId)
        {'StackName': 'this-stack', 'StackId': CURRENT_STACK_ID,
         'Tags': [{'Key': 'cloudzero-stack', 'Value': 'this-stack'}]},
        # this stack's nested stack (excluded by RootId)
        {'StackName': 'this-nested', 'StackId': 'nested-id', 'RootId': CURRENT_STACK_ID,
         'Tags': [{'Key': 'cloudzero-stack', 'Value': 'this-stack'}]},
        # a previously-deployed CloudZero stack (detected)
        {'StackName': 'old-cz-stack', 'StackId': 'old-id',
         'Tags': [{'Key': 'cloudzero-stack', 'Value': 'old-cz-stack'}]},
        # an unrelated stack (no tag -> ignored)
        {'StackName': 'unrelated', 'StackId': 'unrelated-id', 'Tags': []},
    ]}
    app.handler(cfn_event, None)
    assert _output(context)['DetectedLegacyConnectionStacks'] == 'old-cz-stack'


@pytest.mark.unit
def test_handler_survives_legacy_detection_failure(
    context, cfn_event, list_buckets_response,
    describe_report_definitions_client_error, describe_organizations_remote,
):
    context.mock_cur.describe_report_definitions.side_effect = describe_report_definitions_client_error
    context.mock_orgs.describe_organization.return_value = describe_organizations_remote
    context.mock_s3.list_buckets.return_value = list_buckets_response
    context.mock_cf.describe_stacks.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'no DescribeStacks'}}, 'DescribeStacks')
    app.handler(cfn_event, None)
    assert _output(context)['DetectedLegacyConnectionStacks'] == ''
