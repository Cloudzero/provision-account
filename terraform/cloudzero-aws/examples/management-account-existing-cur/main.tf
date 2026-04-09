# Connect a management/payer AWS account to CloudZero using an existing CUR bucket.
# This creates the IAM role with S3 read access to the specified bucket.
# No S3 bucket or CUR report is created.

provider "aws" {
  region = "us-east-1"
}

module "cloudzero" {
  source          = "../../"
  external_id     = var.cloudzero_external_id
  cur_bucket_name = var.cur_bucket_name

  tags = {
    ManagedBy = "terraform"
    Purpose   = "cloudzero"
  }
}

variable "cloudzero_external_id" {
  type        = string
  sensitive   = true
  description = "CloudZero external ID from https://app.cloudzero.com/organization/onboard-accounts/connect?cztabs.connect-accounts=manual"
}

variable "cur_bucket_name" {
  type        = string
  description = "Name of the existing S3 bucket containing your AWS Cost and Usage Report."
}

output "role_arn" {
  value = module.cloudzero.role_arn
}

output "cur_bucket_name" {
  value = module.cloudzero.cur_bucket_name
}
