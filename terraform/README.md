# CloudZero Account Provisioning Terraform Templates for AWS

## Recommended: `cloudzero-aws` Module

Use the unified [`cloudzero-aws`](cloudzero-aws/) module for all AWS account types:

```hcl
# Member / resource account
module "cloudzero" {
  source      = "path/to/cloudzero-aws"
  external_id = "your-external-id"
}

# Management / payer account (creates CUR automatically)
module "cloudzero" {
  source      = "path/to/cloudzero-aws"
  external_id = "your-external-id"
  create_cur  = true
}

# Management / payer account (existing CUR bucket)
module "cloudzero" {
  source          = "path/to/cloudzero-aws"
  external_id     = "your-external-id"
  cur_bucket_name = "my-existing-cur-bucket"
}
```

See the [cloudzero-aws README](cloudzero-aws/README.md) for full documentation, inputs, outputs, examples, and migration instructions.

## Prerequisites

1. Obtain your CloudZero external ID from the [manual account connection page](https://app.cloudzero.com/organization/connections/new/aws/resource/manual).
2. If using `create_cur = true`, the AWS provider must target **us-east-1**.

## After Applying

After `terraform apply`, complete the connection in the CloudZero UI by entering the role ARN output at **Organization > Onboard Accounts > Manual**.

## Deprecated Modules

The following modules are deprecated and should not be used for new deployments:

- [`cloudzero-payer`](cloudzero-payer/) — use `cloudzero-aws` with `cur_bucket_name` or `create_cur` instead
- [`cloudzero-resource`](cloudzero-resource/) — use `cloudzero-aws` without CUR settings instead

## Getting Support

If you have questions or want to report an issue, feel free to open an issue or write to us at support@cloudzero.com.

For the fastest onboarding experience, consider using the automated CloudFormation connection process via the [CloudZero web application](https://app.cloudzero.com).
