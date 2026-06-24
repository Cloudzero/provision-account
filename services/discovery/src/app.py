# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

"""
Discovery custom-resource handler.

Given the AWS account this stack is deployed into, inspect the account and report
back the facts the connected-account stack needs to decide what to provision:

  * Is this a resource connection?    (always yes -- every connected account)
  * Is this a billing connection?     (standalone account, or org management account)
  * Where does this account's CUR live?  (classic Cost & Usage Report or BCM Data Export)
  * Are there older CloudZero stacks already deployed here?  (to guide cleanup)

The flow is deliberately linear and side-effect-light: `handler` validates its input,
calls `discover`, validates the output, and sends it back to CloudFormation. `discover`
gathers raw facts from AWS sources (each isolated so one failure can't sink the others)
and then classifies them. There is no CloudTrail/audit detection -- those connection
types are deprecated.
"""

import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from voluptuous import Any, ExactSequence, Schema, ALLOW_EXTRA, REMOVE_EXTRA

from src import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cur = boto3.client('cur', region_name='us-east-1')  # cur is only in us-east-1
bcm = boto3.client('bcm-data-exports', region_name='us-east-1')  # bcm-data-exports is only in us-east-1
orgs = boto3.client('organizations')
s3 = boto3.client('s3')
cf = boto3.client('cloudformation')


DEFAULT_OUTPUT = {
    'IsResourceConnection': False,
    'IsBillingConnection': False,
    'IsOrganizationMasterAccount': False,
    'IsAccountOutsideOrganization': False,
    'BillingBucketName': None,
    'BillingBucketPath': None,
    'BillingBucketArns': '',
    'BillingReportFormat': 'aws',
    'DetectedLegacyConnectionStacks': '',
}


#####################
#
# Boundary Validation
#
#####################
INPUT_SCHEMA = Schema({
    'event': {
        'RequestType': Any('Create', 'Update', 'Delete'),
        'ResourceProperties': {
            'AccountId': str
        },
        'ResponseURL': str,
        'StackId': str
    }
}, required=True, extra=REMOVE_EXTRA)

OUTPUT_SCHEMA = Schema({
    'output': {
        'IsResourceConnection': bool,
        'IsBillingConnection': bool,
        'IsOrganizationMasterAccount': bool,
        'BillingBucketName': Any(None, str),
        'BillingBucketArns': str,
    },
}, required=True, extra=ALLOW_EXTRA)


#####################
#
# Gather: read raw facts from AWS (each source isolated from the others)
#
#####################
def list_local_bucket_names():
    """Return the set of S3 bucket names owned by this account."""
    try:
        response = s3.list_buckets()
    except ClientError:
        logger.warning('Failed to list S3 buckets', exc_info=True)
        return set()
    return {b['Name'] for b in response.get('Buckets', []) if b.get('Name')}


def list_cur_report_definitions():
    """Return the classic Cost & Usage Report definitions defined in this account."""
    try:
        return cur.describe_report_definitions().get('ReportDefinitions', [])
    except ClientError:
        logger.warning('Failed to access CUR DescribeReportDefinitions', exc_info=True)
        return []


def list_data_export_bucket_names():
    """
    Return the S3 destination buckets of every BCM Data Export in this account.

    CUR 2.0 exports (and any other BCM Data Exports) live here rather than in the
    classic CUR. CloudZero only ingests COST_AND_USAGE_REPORT exports, but we collect
    the S3 destination bucket for *every* export regardless of type so the billing
    connection role's bucket access covers all of them -- a customer can then repoint
    CloudZero at a different export without redeploying this stack. `list_exports` only
    returns export ARNs, so each export is resolved with `get_export` to read its bucket.
    """
    try:
        export_arns = []
        next_token = None
        while True:
            response = bcm.list_exports(**({'NextToken': next_token} if next_token else {}))
            export_arns.extend(ref['ExportArn'] for ref in response.get('Exports', []) if ref.get('ExportArn'))
            next_token = response.get('NextToken')
            if not next_token:
                break
    except (ClientError, BotoCoreError):
        logger.warning('Failed to access BCM Data Exports ListExports', exc_info=True)
        return []

    # Resolve each export independently: a transient failure on one export should not
    # drop the buckets already resolved from the others, so isolate the get_export call
    # per export rather than wrapping the whole loop in a single try/except. Catch
    # BotoCoreError too (e.g. EndpointConnectionError) so connectivity blips degrade
    # gracefully rather than failing the stack.
    buckets = []
    for export_arn in export_arns:
        try:
            export = bcm.get_export(ExportArn=export_arn).get('Export', {})
        except (ClientError, BotoCoreError):
            logger.warning('Failed to access BCM Data Exports GetExport for %s', export_arn, exc_info=True)
            continue
        bucket = export.get('DestinationConfigurations', {}).get('S3Destination', {}).get('S3Bucket')
        if bucket:
            buckets.append(bucket)
    return buckets


def get_organization_master_account_id():
    """Return the org's management account id, or None if not in an org."""
    try:
        return orgs.describe_organization().get('Organization', {}).get('MasterAccountId')
    except ClientError:
        # The account is not a member of an AWS Organization.
        return None


def detect_legacy_connection_stacks(current_stack_id):
    """
    Return the names of other CloudZero stacks already deployed in this account/region.

    A previously-deployed CloudZero connection (an older template generation) is tagged
    `cloudzero-stack`. We surface any such stack other than the one currently deploying
    (and its own nested stacks) so the customer can be guided to remove it once this
    connection is in place. Read-only and best-effort: any failure yields an empty list.
    """
    try:
        names = []
        next_token = None
        while True:
            response = cf.describe_stacks(**({'NextToken': next_token} if next_token else {}))
            for stack in response.get('Stacks', []):
                # Skip the current deployment: the stack itself and any of its nested stacks.
                if stack.get('StackId') == current_stack_id or stack.get('RootId') == current_stack_id:
                    continue
                tags = {t['Key']: t['Value'] for t in stack.get('Tags', [])}
                if 'cloudzero-stack' in tags and stack.get('StackName'):
                    names.append(stack['StackName'])
            next_token = response.get('NextToken')
            if not next_token:
                break
        return names
    except (ClientError, BotoCoreError):
        logger.warning('Failed to detect legacy CloudZero stacks', exc_info=True)
        return []


#####################
#
# CUR report selection
#
#####################
# A CUR report must match one of these schemas to be ingestable by CloudZero. CSV is
# preferred over Parquet, and within a format an "ideal" (resource-tagged, versioned)
# report is preferred over a "minimum" one.
IDEAL_BILLING_REPORT_CSV = Schema({
    'TimeUnit': 'HOURLY',
    'Format': 'textORcsv',
    'Compression': 'GZIP',
    'AdditionalSchemaElements': ExactSequence(['RESOURCES']),
    'S3Bucket': str,
    'S3Prefix': str,
    'S3Region': str,
    'ReportVersioning': 'CREATE_NEW_REPORT',
    'RefreshClosedReports': True,
}, extra=ALLOW_EXTRA, required=True)

IDEAL_BILLING_REPORT_PARQUET = Schema({
    'TimeUnit': 'HOURLY',
    'Format': 'Parquet',
    'Compression': 'Parquet',
    'AdditionalSchemaElements': ExactSequence(['RESOURCES']),
    'S3Bucket': str,
    'S3Prefix': str,
    'S3Region': str,
    'ReportVersioning': 'CREATE_NEW_REPORT',
    'RefreshClosedReports': True,
}, extra=ALLOW_EXTRA, required=True)

MINIMUM_BILLING_REPORT_CSV = Schema({
    'TimeUnit': 'HOURLY',
    'Format': 'textORcsv',
    'Compression': 'GZIP',
    'S3Bucket': str,
    'S3Prefix': str,
    'S3Region': str,
    'RefreshClosedReports': bool,
}, extra=ALLOW_EXTRA, required=True)

MINIMUM_BILLING_REPORT_PARQUET = Schema({
    'TimeUnit': 'HOURLY',
    'Format': 'Parquet',
    'Compression': 'Parquet',
    'S3Bucket': str,
    'S3Prefix': str,
    'S3Region': str,
    'RefreshClosedReports': bool,
}, extra=ALLOW_EXTRA, required=True)

# All CSV tiers are evaluated before any Parquet tier so that CSV wins unconditionally when both formats exist.
# Customers whose Parquet CUR was previously undetected had a CSV CUR created for them by this stack — if
# Parquet were matched on a subsequent stack update, their existing CSV connection could receive duplicate data.
_CUR_CANDIDATE_TIERS = [
    (IDEAL_BILLING_REPORT_CSV, 'aws'),
    (MINIMUM_BILLING_REPORT_CSV, 'aws'),
    (IDEAL_BILLING_REPORT_PARQUET, 'aws_parquet'),
    (MINIMUM_BILLING_REPORT_PARQUET, 'aws_parquet'),
]


def matches_schema(schema, data):
    """True if `data` validates against the voluptuous `schema`."""
    try:
        schema(data)
        return True
    except Exception:
        return False


def select_ingest_cur(report_definitions, local_bucket_names):
    """
    Pick the single CUR report CloudZero will ingest, preferring CSV over Parquet and
    ideal over minimum (see `_CUR_CANDIDATE_TIERS`). Only reports whose bucket is owned
    by this account are eligible.

    Returns (bucket_name, bucket_path, billing_report_format); all-None / 'aws' when none.
    """
    for schema, billing_report_format in _CUR_CANDIDATE_TIERS:
        for report in report_definitions:
            if report.get('S3Bucket') in local_bucket_names and matches_schema(schema, report):
                bucket_name = report['S3Bucket']
                bucket_path = f"{report.get('S3Prefix', '')}/{report.get('ReportName', '')}"
                return bucket_name, bucket_path, billing_report_format
    return None, None, 'aws'


def all_local_billing_bucket_names(report_definitions, data_export_buckets, local_bucket_names):
    """
    Every locally-owned bucket referenced by any CUR report or BCM Data Export.

    Deliberately schema-agnostic: a bucket referenced by any billing report/export is
    legitimate billing storage, so the billing connection role gets s3:Get/List on all
    of them. This lets a customer switch CloudZero between report formats (CSV/Parquet/
    CUR 2.0) without redeploying this stack. The schema filter in `select_ingest_cur`
    only governs which report CloudZero currently ingests, not which buckets are legitimate.
    """
    report_buckets = {r['S3Bucket'] for r in report_definitions if isinstance(r.get('S3Bucket'), str)}
    export_buckets = {b for b in data_export_buckets if isinstance(b, str)}
    return sorted((report_buckets | export_buckets) & local_bucket_names)


def format_bucket_arns(bucket_names):
    """Render bucket names as a comma-separated list of `bucket` and `bucket/*` ARNs."""
    arns = []
    for name in bucket_names:
        arns.append(f'arn:aws:s3:::{name}')
        arns.append(f'arn:aws:s3:::{name}/*')
    return ','.join(arns)


#####################
#
# Classification
#
#####################
def discover(account_id, current_stack_id):
    """Gather account facts and classify the account for CloudZero onboarding."""
    local_bucket_names = list_local_bucket_names()
    report_definitions = list_cur_report_definitions()
    data_export_buckets = list_data_export_bucket_names()
    master_account_id = get_organization_master_account_id()
    legacy_stacks = detect_legacy_connection_stacks(current_stack_id)

    is_outside_organization = master_account_id is None
    is_organization_master = account_id == master_account_id
    # A standalone account (no org) pays its own bill; in an org, the management account
    # is the billing account. Either way that account owns the consolidated CUR.
    is_billing = is_outside_organization or is_organization_master

    ingest_bucket, ingest_path, billing_report_format = select_ingest_cur(report_definitions, local_bucket_names)
    billing_bucket_arns = format_bucket_arns(
        all_local_billing_bucket_names(report_definitions, data_export_buckets, local_bucket_names))

    return {
        'IsResourceConnection': True,
        'IsBillingConnection': is_billing,
        'IsOrganizationMasterAccount': is_organization_master,
        'IsAccountOutsideOrganization': is_outside_organization,
        'BillingBucketName': ingest_bucket,
        'BillingBucketPath': ingest_path,
        'BillingBucketArns': billing_bucket_arns,
        'BillingReportFormat': billing_report_format,
        'DetectedLegacyConnectionStacks': ','.join(legacy_stacks),
    }


#####################
#
# Handler
#
#####################
def handler(event, context, **kwargs):
    status = cfnresponse.SUCCESS
    output = DEFAULT_OUTPUT
    try:
        # Avoid logging the full event/output: they carry account-identifying fields
        # that CodeQL flags as clear-text logging of sensitive data.
        logger.info('Processing %s discovery request', event.get('RequestType'))
        validated = INPUT_SCHEMA({'event': event})['event']
        account_id = validated['ResourceProperties']['AccountId']
        output = OUTPUT_SCHEMA({'output': discover(account_id, validated['StackId'])})['output']
    except Exception as err:
        logger.exception(err)
    finally:
        # Static message: interpolating the classification flags trips CodeQL's
        # clear-text-logging "private data" heuristic on the variable names.
        logger.info('Discovery complete')
        cfnresponse.send(event, context, status, output, event.get('PhysicalResourceId'))
