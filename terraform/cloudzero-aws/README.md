# CloudZero AWS Account Connection — Terraform Module

Connects an AWS account to CloudZero by creating the cross-account IAM role and (optionally) a Cost and Usage Report. This is a unified module that replaces the separate `cloudzero-payer` and `cloudzero-resource` modules.

## Usage

### Member / Resource Account

```hcl
module "cloudzero" {
  source      = "path/to/cloudzero-aws"
  external_id = "your-external-id"
}
```

### Management / Payer Account (new CUR)

```hcl
module "cloudzero" {
  source      = "path/to/cloudzero-aws"
  external_id = "your-external-id"
  create_cur  = true
}
```

### Management / Payer Account (existing CUR bucket)

```hcl
module "cloudzero" {
  source          = "path/to/cloudzero-aws"
  external_id     = "your-external-id"
  cur_bucket_name = "my-existing-cur-bucket"
}
```

## Prerequisites

1. Obtain your CloudZero external ID from the [manual account connection page](https://app.cloudzero.com/organization/connections/new/aws/resource/manual).
2. If using `create_cur = true`, the AWS provider must target **us-east-1** (CUR report definitions can only be created in us-east-1).

## After Applying

After `terraform apply`, you must complete the connection in the CloudZero UI:

1. Go to **Organization > Onboard Accounts > Manual**
2. Enter the role ARN from the `role_arn` output
3. Click **Connect**

> This manual step will be eliminated when the CloudZero Terraform provider is available, enabling automatic account registration via the CloudZero API.

## IAM Permissions

This module creates a read-only IAM role with permissions matching the CloudZero CloudFormation onboarding template:

**Inline policy statements:**
- Cost monitoring (billing, CUR, Cost Explorer, pricing, organizations)
- Activity monitoring (CloudTrail, health, service quotas, resource groups, tagging)
- Reserved capacity (EC2, RDS, DynamoDB, ElastiCache, OpenSearch, Redshift)
- Container Insights (CloudWatch Logs for `/aws/containerinsights/*`)
- CloudWatch metrics (autoscaling, cloudwatch)
- Cost Optimization Hub
- CloudFormation read access
- S3 CUR bucket access (management accounts only)

**Managed policies:**
- `ComputeOptimizerReadOnlyAccess`
- `ViewOnlyAccess`
- `AWSBillingReadOnlyAccess`
- `CloudWatchReadOnlyAccess`

Individual policy blocks can be disabled via feature toggle variables (e.g., `enable_container_insights = false`).

## Inputs

| Name | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| `external_id` | `string` | — | yes | CloudZero external ID for cross-account trust |
| `create_cur` | `bool` | `false` | no | Create S3 bucket and CUR report definition |
| `cur_bucket_name` | `string` | `""` | no | Existing CUR bucket name (mutually exclusive with `create_cur`) |
| `role_name` | `string` | `"cloudzero-access"` | no | IAM role name |
| `role_path` | `string` | `"/"` | no | IAM role path |
| `permissions_boundary` | `string` | `null` | no | Permissions boundary ARN |
| `tags` | `map(string)` | `{}` | no | Tags for all resources |
| `enable_activity_monitoring` | `bool` | `true` | no | Toggle activity monitoring policy |
| `enable_container_insights` | `bool` | `true` | no | Toggle Container Insights policy |
| `enable_cloudwatch_metrics` | `bool` | `true` | no | Toggle CloudWatch metrics policy |
| `enable_reserved_capacity` | `bool` | `true` | no | Toggle reserved capacity policy |
| `enable_optimization_hub` | `bool` | `true` | no | Toggle Cost Optimization Hub policy |
| `enable_cloudformation_access` | `bool` | `true` | no | Toggle CloudFormation read policy |
| `additional_managed_policy_arns` | `list(string)` | `[]` | no | Extra managed policies to attach |

See `variables.tf` for the full list of CUR configuration variables.

## Outputs

| Name | Description |
|------|-------------|
| `role_arn` | ARN of the CloudZero cross-account IAM role |
| `role_name` | Name of the IAM role |
| `role_id` | Unique ID of the IAM role |
| `account_id` | AWS account ID |
| `is_management_account` | Whether configured as management account |
| `cur_bucket_name` | CUR bucket name (null for member accounts) |
| `cur_bucket_arn` | CUR bucket ARN (null if not created by this module) |
| `cur_report_name` | CUR report name (null if not created by this module) |

## Migration from Old Modules

### From `cloudzero-payer`

```hcl
# Old
module "cloudzero" {
  source               = "../cloudzero-payer"
  cloudzero_external_id = "your-id"
  AWS_CUR_bucket        = "your-bucket"
}

# New
module "cloudzero" {
  source          = "../cloudzero-aws"
  external_id     = "your-id"
  cur_bucket_name = "your-bucket"
}
```

To migrate state without recreating the IAM role:

```bash
terraform state mv 'module.cloudzero.aws_iam_role.cloudzero' 'module.cloudzero.aws_iam_role.cloudzero'
terraform state mv 'module.cloudzero.aws_iam_role_policy.CloudZero' 'module.cloudzero.aws_iam_role_policy.cloudzero'
terraform state mv 'module.cloudzero.aws_iam_role_policy_attachment.compute_optimizer_access' 'module.cloudzero.aws_iam_role_policy_attachment.compute_optimizer'
terraform state mv 'module.cloudzero.aws_iam_role_policy_attachment.view_only_access' 'module.cloudzero.aws_iam_role_policy_attachment.view_only'
```

### From `cloudzero-resource`

```hcl
# Old
module "cloudzero" {
  source               = "../cloudzero-resource"
  cloudzero_external_id = "your-id"
}

# New
module "cloudzero" {
  source      = "../cloudzero-aws"
  external_id = "your-id"
}
```
