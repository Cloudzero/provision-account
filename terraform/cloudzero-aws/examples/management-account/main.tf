# Connect a management/payer AWS account to CloudZero with automatic CUR creation.
# This creates the IAM role, S3 bucket, and Cost and Usage Report definition.
#
# IMPORTANT: The AWS provider must target us-east-1 for CUR report creation.

provider "aws" {
  region = "us-east-1"
}

module "cloudzero" {
  source      = "../../"
  external_id = var.cloudzero_external_id
  create_cur  = true

  # Optional: customize CUR settings
  # cur_time_unit        = "HOURLY"
  # cur_bucket_name_prefix = "mycompany-cur-cloudzero"

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

output "cur_bucket_name" {
  value = module.cloudzero.cur_bucket_name
}

output "cur_report_name" {
  value = module.cloudzero.cur_report_name
}
