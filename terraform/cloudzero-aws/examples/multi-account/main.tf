# Connect multiple AWS accounts to CloudZero using for_each.
#
# This example assumes each account has a named AWS CLI profile.
# Adjust the provider configuration to match your authentication setup
# (e.g., assume_role, SSO, etc.).
#
# IMPORTANT: The AWS provider must target us-east-1 for accounts with CUR creation.

variable "external_ids" {
  type        = map(string)
  sensitive   = true
  description = "Map of account name to CloudZero external ID."
}

# Note: Terraform does not support dynamic provider configurations with for_each.
# In practice, you would use Terragrunt, workspaces, or separate root modules
# per account. This example illustrates the module interface for each account type.

# Management account
provider "aws" {
  alias   = "management"
  region  = "us-east-1"
  profile = "management-account"
}

module "cloudzero_management" {
  source      = "../../"
  external_id = var.external_ids["management"]
  create_cur  = true

  providers = {
    aws = aws.management
  }

  tags = {
    ManagedBy = "terraform"
    Purpose   = "cloudzero"
    Account   = "management"
  }
}

# Member account
provider "aws" {
  alias   = "production"
  region  = "us-east-1"
  profile = "prod-account"
}

module "cloudzero_production" {
  source      = "../../"
  external_id = var.external_ids["production"]

  providers = {
    aws = aws.production
  }

  tags = {
    ManagedBy = "terraform"
    Purpose   = "cloudzero"
    Account   = "production"
  }
}

output "management_role_arn" {
  value = module.cloudzero_management.role_arn
}

output "management_cur_bucket" {
  value = module.cloudzero_management.cur_bucket_name
}

output "production_role_arn" {
  value = module.cloudzero_production.role_arn
}
