# DEPRECATED

This module is deprecated. Use [`cloudzero-aws`](../cloudzero-aws/) instead.

## Migration

```hcl
# Old (this module)
module "cloudzero" {
  source                = "../cloudzero-resource"
  cloudzero_external_id = "your-id"
}

# New (cloudzero-aws)
module "cloudzero" {
  source      = "../cloudzero-aws"
  external_id = "your-id"
}
```

The new module adds:
- Missing managed policies (`AWSBillingReadOnlyAccess`, `CloudWatchReadOnlyAccess`)
- Outputs (role ARN, account ID)
- Feature toggles for individual policy blocks
- Permissions boundary support
- Configurable role name, path, and tags

See the [cloudzero-aws README](../cloudzero-aws/README.md) for full documentation and state migration instructions.
