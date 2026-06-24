# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

"""
Custom-resource handler that writes a cleanup guide into the connected CUR bucket root.

When a customer moves from an older CloudZero stack to this one, the new connection
re-adopts their existing Cost and Usage Report, so no billing data is moved or lost.
This handler drops a short markdown guide (`CLOUDZERO_CLEANUP_GUIDE.md`) at the root of
the connected CUR bucket, listing the older stack(s) that were detected and the safe
steps to remove them.

It is a no-op when there is no target bucket or nothing to clean up, never deletes
anything, and is best-effort: a failure to write is logged but never fails the stack.
"""

import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

GUIDE_KEY = 'CLOUDZERO_CLEANUP_GUIDE.md'


def build_guide(legacy_stacks):
    """Render the markdown cleanup guide listing the detected legacy stack(s)."""
    stacks = '\n'.join(f'- `{name}`' for name in legacy_stacks)
    return f"""# CloudZero connection cleanup

A new CloudZero connection has been established in this account and has re-adopted your
existing Cost and Usage Report, so no billing data was moved or lost.

You can now remove the previously-deployed CloudZero CloudFormation stack(s):

{stacks}

## How to remove

1. Open the AWS CloudFormation console in this account and region.
2. Confirm the new CloudZero connection is reporting healthy in the CloudZero platform.
3. Select each stack listed above and choose **Delete**.

Your CUR S3 bucket and its data are retained; deleting the old stack only removes the
old cross-account role and related resources.
"""


def _bucket_client(bucket):
    """An S3 client in the bucket's own region (PutObject is region-sensitive)."""
    location = s3.get_bucket_location(Bucket=bucket).get('LocationConstraint') or 'us-east-1'
    return boto3.client('s3', region_name=location)


def handler(event, context, **kwargs):
    status = cfnresponse.SUCCESS
    try:
        request_type = event.get('RequestType')
        properties = event.get('ResourceProperties', {})
        bucket = properties.get('BucketName')
        bucket = None if bucket in (None, '', 'null') else bucket
        legacy_stacks = [s for s in (properties.get('DetectedLegacyConnectionStacks') or '').split(',') if s]

        if request_type in ('Create', 'Update') and bucket and legacy_stacks:
            logger.info('Writing cleanup guide to s3://%s/%s', bucket, GUIDE_KEY)
            _bucket_client(bucket).put_object(
                Bucket=bucket,
                Key=GUIDE_KEY,
                Body=build_guide(legacy_stacks).encode('utf-8'),
                ContentType='text/markdown',
            )
        else:
            # Nothing to do: a delete, no connected bucket, or no legacy stack to clean up.
            logger.info('Skipping cleanup guide (request=%s, has_bucket=%s, legacy=%d)',
                        request_type, bool(bucket), len(legacy_stacks))
    except (ClientError, BotoCoreError):
        logger.warning('Failed to write cleanup guide', exc_info=True)
    finally:
        cfnresponse.send(event, context, status, {}, event.get('PhysicalResourceId'))
