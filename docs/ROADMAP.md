# Roadmap

Planned changes to the CloudZero account-provisioning templates. Items here describe direction and are subject to reprioritization.

## Planned

### StackSet-friendly resource-owner template

**Tracking issue:** [#77](https://github.com/Cloudzero/provision-account/issues/77)

A flat, single-file CloudFormation template suitable for deployment via AWS Organizations StackSets with service-managed permissions, so customers can onboard many member accounts in one operation. The current `services/connected_account.yaml` orchestrates nested stacks, which StackSets do not support in service-managed mode.

The new template will:

- Contain no `AWS::CloudFormation::Stack` resources (fully flat).
- Create the cross-account IAM role with the tiered inline policy that the nested-stack path uses today (see `policies/README.md`).
- Use a deterministic role name and path so CloudZero can locate the role in each member account without per-account registration callbacks.
- Target the resource-owner use case. Master payer accounts continue to use the dedicated template.

### Single inline policy for payer and resource-owner roles

`policies/master_payer.json` and `policies/resource_owner.json` are maintained as two separate files today. The only material difference between them is the CUR S3 bucket statement (payer-only). Direction: collapse to a single canonical policy with the bucket statement applied conditionally for payer deployments.

## Planned removals

### `services/account_type/audit.yaml` and `services/account_type/cloudtrail_owner.yaml`

The audit and CloudTrail owner account templates will be removed in a future release. These templates provision SQS/SNS and CloudTrail-bucket IAM resources that are no longer part of the standard CloudZero onboarding flow.

Existing deployments that include these stacks continue to function; new deployments should not depend on them.
