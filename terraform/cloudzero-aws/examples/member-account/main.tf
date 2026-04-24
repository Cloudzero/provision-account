# Connect a member/resource AWS account to CloudZero.
# This creates the cross-account IAM role only (no CUR setup).

provider "aws" {
  region = "us-east-1"
}

module "cloudzero" {
  source      = "../../"
  external_id = var.cloudzero_external_id

  tags = {
    ManagedBy = "terraform"
    Purpose   = "cloudzero"
  }
}

variable "cloudzero_external_id" {
  type        = string
  sensitive   = true
  description = "CloudZero external ID from https://app.cloudzero.com/organization/connections/new/aws/resource/manual"
}

output "role_arn" {
  value = module.cloudzero.role_arn
}

output "account_id" {
  value = module.cloudzero.account_id
}
