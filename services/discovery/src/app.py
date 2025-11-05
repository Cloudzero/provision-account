# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

from pprint import pformat
import logging

import boto3
from botocore.exceptions import ClientError
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, ExactSequence, Schema, ALLOW_EXTRA, REMOVE_EXTRA

from src import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ct = boto3.client('cloudtrail')
cur = boto3.client('cur', region_name='us-east-1')  # cur is only in us-east-1
orgs = boto3.client('organizations')
s3 = boto3.client('s3')

DEFAULT_OUTPUT = {
    'AuditCloudTrailBucketPrefix': None,
    'AuditCloudTrailBucketName': None,
    'RemoteCloudTrailBucket': True,
    'CloudTrailSNSTopicArn': None,
    'CloudTrailTrailArn': None,
    'IsOrganizationTrail': None,
    'IsOrganizationMasterAccount': False,
    'VisibleCloudTrailArns': None,
    'IsAuditAccount': False,
    'IsCloudTrailOwnerAccount': False,
    'IsResourceOwnerAccount': False,
    'IsMasterPayerAccount': False,
    'MasterPayerBillingBucketName': None,
    'MasterPayerBillingBucketPath': None,
    'IsAccountOutsideOrganization': False,
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
        'IsAuditAccount': bool,
        'AuditCloudTrailBucketName': Any(None, str),
        'IsResourceOwnerAccount': bool,
        'IsCloudTrailOwnerAccount': bool,
        'CloudTrailSNSTopicArn': Any(None, str),
        'IsMasterPayerAccount': bool,
        'MasterPayerBillingBucketName': Any(None, str),
    },
}, required=True, extra=ALLOW_EXTRA)

DEFAULT_PAYER_REPORTS = {'is_master_payer': False, 'report_definitions': []}
NOT_IN_ORGANIZATION_RESPONSE = {}

event_account_id = get_in(['event', 'ResourceProperties', 'AccountId'])
coeffects_traillist = get_in(['coeffects', 'cloudtrail', 'trailList'], default=[])
coeffects_buckets = get_in(['coeffects', 's3', 'Buckets'], default=[])
coeffects_payer_reports = get_in(['coeffects', 'cur'], default=DEFAULT_PAYER_REPORTS)
coeffects_master_account_id = get_in(['coeffects', 'organizations', 'Organization', 'MasterAccountId'])
output_is_organization_master = get_in(['output', 'IsOrganizationMasterAccount'])
output_is_account_outside_organization = get_in(['output', 'IsAccountOutsideOrganization'])


#####################
#
# Coeffects, i.e. from the outside world
#
#####################
def coeffects(world):
    return pipe(world,
                coeffects_cloudtrail,
                coeffects_s3,
                coeffects_cur,
                coeffects_organizations)


def coeffect(name):
    def d(f):
        def w(world):
            data = {}
            try:
                data = f(world)
            except Exception:
                logger.warning(f'Failed to get {name} information.', exc_info=True)
            return assoc_in(world, ['coeffects', name], data)
        return w
    return d


@coeffect('cloudtrail')
def coeffects_cloudtrail(world):
    response = ct.describe_trails()
    return keyfilter(lambda x: x in {'trailList'}, response)


@coeffect('s3')
def coeffects_s3(world):
    response = s3.list_buckets()
    return keyfilter(lambda x: x in {'Buckets'}, response)


@coeffect('cur')
def coeffects_cur(world):
    try:
        return {
            'report_definitions': cur.describe_report_definitions().get('ReportDefinitions', []),
        }
    except ClientError:
        logger.warning('Failed to access CUR DescribeReportDefinitions', exc_info=True)
        return DEFAULT_PAYER_REPORTS


@coeffect('organizations')
def coeffects_organizations(world):
    try:
        response = orgs.describe_organization()
        return keyfilter(lambda x: x in {'Organization'}, response)
    except ClientError:
        return NOT_IN_ORGANIZATION_RESPONSE


#####################
#
# Business Logic
#
#####################
MINIMUM_CLOUDTRAIL_CONFIGURATION = Schema({
    "S3BucketName": str,
    "SnsTopicName": str,
    "SnsTopicARN": str,
    "IsMultiRegionTrail": True,
    "TrailARN": str,
}, extra=ALLOW_EXTRA, required=True)


IDEAL_CLOUDTRAIL_CONFIGURATION = MINIMUM_CLOUDTRAIL_CONFIGURATION.extend({
    "IsOrganizationTrail": True,
}, extra=ALLOW_EXTRA, required=True)


def safe_check(schema, data):
    try:
        return schema(data)
    except Exception:
        logger.debug(f'Data {pformat(data)} did not match schema {schema}', exc_info=True)
        return None


def keep_valid(schema, xs):
    return [
        y for y in [safe_check(schema, x) for x in xs]
        if y is not None
    ]


def get_first_valid_trail(world):
    trails = coeffects_traillist(world)
    logger.info(f'Found these CloudTrails: {trails}')
    valid_trails = keep_valid(IDEAL_CLOUDTRAIL_CONFIGURATION, trails) or keep_valid(MINIMUM_CLOUDTRAIL_CONFIGURATION, trails)
    logger.info(f'Found these _valid_ CloudTrails: {valid_trails}')
    return valid_trails[0] if valid_trails else {}


def discover_audit_account(world):
    trail = get_first_valid_trail(world)
    trail_bucket = trail.get('S3BucketName')
    local_buckets = {x['Name'] for x in coeffects_buckets(world)}
    output = {
        'IsAuditAccount': trail_bucket in local_buckets,
        'RemoteCloudTrailBucket': trail_bucket not in local_buckets,
        'AuditCloudTrailBucketName': trail_bucket,
        'AuditCloudTrailBucketPrefix': trail.get('S3KeyPrefix'),
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def discover_connected_account(world):
    output = {
        'IsResourceOwnerAccount': True,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def get_visible_cloudtrail_arns(world):
    visible_trail_arns = [x.get('TrailARN')
                          for x in coeffects_traillist(world)]
    return ','.join(visible_trail_arns) if visible_trail_arns else None


def discover_cloudtrail_account(world):
    visible_trails = get_visible_cloudtrail_arns(world)
    trail = get_first_valid_trail(world)
    trail_topic = trail.get('SnsTopicARN')
    account_id = trail_topic.split(':')[4] if trail_topic else None
    output = {
        'IsCloudTrailOwnerAccount': account_id == event_account_id(world),
        'IsOrganizationTrail': trail.get('IsOrganizationTrail'),
        'CloudTrailSNSTopicArn': trail_topic,
        'CloudTrailTrailArn': trail.get('TrailARN'),
        'VisibleCloudTrailArns': visible_trails,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


IDEAL_BILLING_REPORT = Schema({
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

MINIMUM_BILLING_REPORT = Schema({
    'TimeUnit': Any('HOURLY', 'DAILY'),
    'Format': 'textORcsv',
    'Compression': 'GZIP',
    'S3Bucket': str,
    'S3Prefix': str,
    'S3Region': str,
    'RefreshClosedReports': bool,
}, extra=ALLOW_EXTRA, required=True)


def get_first_valid_report_definition(valid_report_definitions, default=None):
    return valid_report_definitions[0] if any(valid_report_definitions) else default


def get_cur_bucket_if_local(world, report_definitions):
    logger.info(f'Found these ReportDefinitions: {report_definitions}')
    local_buckets = {x['Name'] for x in coeffects_buckets(world)}

    # Try to find ideal reports first (with CREATE_NEW_REPORT)
    ideal_report_definitions = keep_valid(IDEAL_BILLING_REPORT, report_definitions)
    logger.info(f'Found these _ideal_ ReportDefinitions: {ideal_report_definitions}')
    ideal_local_report_definitions = [x for x in ideal_report_definitions if x['S3Bucket'] in local_buckets]
    logger.info(f'Found these _ideal local_ ReportDefinitions: {ideal_local_report_definitions}')

    # Fall back to minimum requirements if no ideal reports found
    if not ideal_local_report_definitions:
        logger.info('No ideal reports found, falling back to minimum requirements')
        valid_report_definitions = keep_valid(MINIMUM_BILLING_REPORT, report_definitions)
        logger.info(f'Found these _valid_ ReportDefinitions: {valid_report_definitions}')
        valid_local_report_definitions = [x for x in valid_report_definitions if x['S3Bucket'] in local_buckets]
        logger.info(f'Found these _valid local_ ReportDefinitions: {valid_local_report_definitions}')
        first_valid_local = get_first_valid_report_definition(valid_local_report_definitions, default={})
    else:
        first_valid_local = get_first_valid_report_definition(ideal_local_report_definitions, default={})

    bucket_name = first_valid_local.get('S3Bucket')
    bucket_path = f"{first_valid_local.get('S3Prefix', '')}/{first_valid_local.get('ReportName', '')}" if bucket_name else None
    return (bucket_name, bucket_path)


def discover_master_payer_account(world):
    is_account_not_in_organization = output_is_account_outside_organization(world)
    is_account_organization_master_account = output_is_organization_master(world)
    is_master_payer = is_account_not_in_organization or is_account_organization_master_account
    report_definitions = coeffects_payer_reports(world)['report_definitions']
    (bucket_name, bucket_path) = get_cur_bucket_if_local(world, report_definitions)
    output = {
        'IsMasterPayerAccount': is_master_payer,
        'MasterPayerBillingBucketName': bucket_name,
        'MasterPayerBillingBucketPath': bucket_path,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def discover_organization_master_account(world):
    account_id = event_account_id(world)
    master_account_id = coeffects_master_account_id(world)

    output = {
        'IsOrganizationMasterAccount': account_id == master_account_id,
        'IsAccountOutsideOrganization': master_account_id is None,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def discover_account_types(world):
    return pipe(world,
                discover_audit_account,
                discover_connected_account,
                discover_cloudtrail_account,
                discover_organization_master_account,
                discover_master_payer_account)


#####################
#
# Handler
#
#####################
def handler(event, context, **kwargs):
    status = cfnresponse.SUCCESS
    world = {}
    try:
        logger.info(f'Processing event {event}')
        world = pipe({'event': event, 'kwargs': kwargs},
                     INPUT_SCHEMA,
                     coeffects,
                     discover_account_types,
                     OUTPUT_SCHEMA)
    except Exception as err:
        logger.exception(err)
    finally:
        output = world.get('output', DEFAULT_OUTPUT)
        logger.info(f'Sending output {output}')
        cfnresponse.send(event, context, status, output, event.get('PhysicalResourceId'))
