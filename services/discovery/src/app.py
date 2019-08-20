# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

from pprint import pformat
import boto3
import cfnresponse
from toolz.curried import assoc_in, get_in, keyfilter, merge, pipe, update_in
from voluptuous import Any, ExactSequence, Schema, ALLOW_EXTRA, REMOVE_EXTRA


import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


ct = boto3.client('cloudtrail')
cur = boto3.client('cur', region_name='us-east-1')  # cur is only in us-east-1
s3 = boto3.client('s3')

DEFAULT_OUTPUT = {
    'AuditCloudTrailBucketPrefix': None,
    'AuditCloudTrailBucketName': None,
    'RemoteCloudTrailBucket': True,
    'CloudTrailSNSTopicArn': None,
    'CloudTrailTrailArn': None,
    'VisibleCloudTrailArns': None,
    'IsAuditAccount': False,
    'IsCloudTrailOwnerAccount': False,
    'IsResourceOwnerAccount': False,
    'IsMasterPayerAccount': False,
    'MasterPayerBillingBucketName': None,
    'MasterPayerBillingBucketPath': None,
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

event_account_id = get_in(['event', 'ResourceProperties', 'AccountId'])
coeffects_traillist = get_in(['coeffects', 'cloudtrail', 'trailList'], default=[])


#####################
#
# Coeffects, i.e. from the outside world
#
#####################
def coeffects(world):
    return pipe(world,
                coeffects_cloudtrail,
                coeffects_s3,
                coeffects_cur)


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
    response = cur.describe_report_definitions()
    return keyfilter(lambda x: x in {'ReportDefinitions'}, response)


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
    local_buckets = {x['Name'] for x in get_in(['coeffects', 's3', 'Buckets'], world, [])}
    output = {
        'IsAuditAccount': trail_bucket in local_buckets,
        'RemoteCloudTrailBucket': not (trail_bucket in local_buckets),
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
        'CloudTrailSNSTopicArn': trail_topic,
        'CloudTrailTrailArn': trail.get('TrailARN'),
        'VisibleCloudTrailArns': visible_trails,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


MINIMUM_BILLING_REPORT = Schema({
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


def get_first_valid_report_definition(valid_report_definitions, default=None):
    return valid_report_definitions[0] if any(valid_report_definitions) else default


def discover_master_payer_account(world):
    report_definitions = get_in(['coeffects', 'cur', 'ReportDefinitions'], world, [])
    logger.info(f'Found these ReportDefinitions: {report_definitions}')
    local_buckets = {x['Name'] for x in get_in(['coeffects', 's3', 'Buckets'], world, [])}
    valid_report_definitions = keep_valid(MINIMUM_BILLING_REPORT, report_definitions)
    logger.info(f'Found these _valid_ ReportDefinitions: {valid_report_definitions}')
    first_valid = get_first_valid_report_definition(valid_report_definitions, default={})
    valid_local_report_definitions = [x for x in valid_report_definitions if x['S3Bucket'] in local_buckets]
    logger.info(f'Found these _valid local_ ReportDefinitions: {valid_local_report_definitions}')
    local = any(valid_local_report_definitions)
    first_valid_local = get_first_valid_report_definition(valid_local_report_definitions, default=first_valid)
    bucket_name = first_valid_local.get('S3Bucket')
    bucket_path = f"{first_valid_local.get('S3Prefix', '')}/{first_valid_local.get('ReportName', '')}" if bucket_name else None
    output = {
        'IsMasterPayerAccount': local,
        'MasterPayerBillingBucketName': bucket_name,
        'MasterPayerBillingBucketPath': bucket_path,
    }
    return update_in(world, ['output'], lambda x: merge(x or {}, output))


def discover_account_types(world):
    return pipe(world,
                discover_audit_account,
                discover_connected_account,
                discover_cloudtrail_account,
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
