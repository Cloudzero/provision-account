# IAM Policies

This folder holds the canonical IAM permission documents CloudZero uses to read cost and usage data from a customer AWS account.

## Files

| File | Purpose |
|---|---|
| `master_payer.json` | Inline permissions for the role in a master payer (billing) account. |
| `resource_owner.json` | Inline permissions for the role in a linked/resource-owner account. |
| `managed.json` | The AWS managed policies attached alongside the inline policy. |

The permission sets in `master_payer.json` and `resource_owner.json` are mirrored in the deployable templates under `services/account_type/*.yaml` (CloudFormation) and `terraform/cloudzero-*/main.tf` (Terraform). **The JSON here is the source of truth** — any change must be propagated to all three formats.

## Philosophy

1. **Least privilege, read-only.** Every action is a read/list/describe. No write, no mutate, no decrypt.
2. **Managed policies provide broad read-only coverage.** The role has `CloudWatchReadOnlyAccess`, `ComputeOptimizerReadOnlyAccess`, `AWSBillingReadOnlyAccess`, and `ViewOnlyAccess` attached (see `managed.json`). These grant the cross-service read surface CloudZero relies on.
3. **The inline policy encodes the permissions CloudZero depends on directly.** Each statement corresponds to a capability the platform uses; the managed policies extend coverage across the broader AWS service surface.
4. **Wildcards over enumeration.** We use `service:Verb*` (e.g., `ce:Get*`) rather than enumerating individual API calls. This keeps the policy stable when AWS adds new read APIs within a verb family.
5. **Scope resources when possible.** Statements that can be scoped to specific ARNs (S3 billing bucket, containerinsights log groups, the CloudZero role path) are; statements whose actions don't support resource-level permissions use `Resource: "*"`.

## Sid prefix convention

Statements are organized by purpose, signaled by Sid prefix:

- `CZTier0*` — cost and usage data ingestion (CUR bucket, billing, reserved instances, savings plans).
- `CZTier1*` — cost optimization signals (Compute Optimizer, Cost Optimization Hub, Trusted Advisor, Health, pricing, organizations and tagging metadata, Container Insights logs).
- `CZTier2*` — operational visibility (CloudTrail, CloudWatch metrics, service quotas, CloudFormation, IAM self-inspection).

The prefix helps engineers navigate the policy. Every statement is part of what CloudZero uses in production.

## Conventions

- **`Sid` format**: `CZTier<0|1|2><DescriptiveName><YYYYMMDD>`. The date is the day the statement was last materially changed. Alphabetizing actions or fixing formatting does **not** bump the date; changing actions or the resource scope does.
- **Action ordering**: alphabetical within each statement. Makes diffs minimal and reviews mechanical.
- **Statement grouping**: one `Sid` per logical capability. Don't combine unrelated permissions into a single statement.
- **JSON formatting**: 2-space indent, trailing newline.

## Adding a permission

1. Decide whether the new action fits an existing statement (same capability, same resource scope) or warrants a new one. Place it in the tier (`CZTier0*`/`CZTier1*`/`CZTier2*`) that matches its purpose.
2. Add it alphabetically within the chosen statement.
3. If the statement's action set changed, update its `Sid` date.
4. Propagate the identical change to:
   - `services/account_type/master_payer.yaml` and `resource_owner.yaml`
   - `terraform/cloudzero-payer/main.tf` and `cloudzero-resource/main.tf`
5. Prefer scoping to CloudZero-relevant resources where AWS supports resource-level permissions. When the action only works with `Resource: "*"` and the managed policy layer already grants it, consider whether the inline addition is necessary at all.

## Removing a permission

Before removing: confirm no CloudZero service path depends on it. Removals should bump the enclosing statement's `Sid` date.

## Long-term direction

`master_payer.json` and `resource_owner.json` exist as two separate files today for historical reasons. The only material difference is the CUR S3 bucket Sid (payer-only). Future work: collapse to a single policy used by both account types, with the bucket Sid conditional on payer.
