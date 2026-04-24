# DEPRECATED

This module is deprecated. Use [`cloudzero-aws`](../cloudzero-aws/) instead.

## Migration

```hcl
# Old (this module)
module "cloudzero" {
  source                = "../cloudzero-payer"
  cloudzero_external_id = "your-id"
  AWS_CUR_bucket        = "your-bucket"
}

# New (cloudzero-aws)
module "cloudzero" {
  source          = "../cloudzero-aws"
  external_id     = "your-id"
  cur_bucket_name = "your-bucket"
}
```

The new module adds:
- CUR report and S3 bucket creation (optional)
- Missing managed policies (`AWSBillingReadOnlyAccess`, `CloudWatchReadOnlyAccess`)
- Outputs (role ARN, account ID, CUR bucket)
- Feature toggles for individual policy blocks
- Permissions boundary support
- Configurable role name, path, and tags

See the [cloudzero-aws README](../cloudzero-aws/README.md) for full documentation and state migration instructions.
