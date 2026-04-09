# ---------------------------------------------------------------------------------------------------------------------
# Required
# ---------------------------------------------------------------------------------------------------------------------

variable "external_id" {
  type        = string
  sensitive   = true
  description = "The CloudZero-provided external ID for cross-account role assumption. Found at https://app.cloudzero.com/organization/onboard-accounts/connect?cztabs.connect-accounts=manual"
}

# ---------------------------------------------------------------------------------------------------------------------
# CUR Toggle
# ---------------------------------------------------------------------------------------------------------------------

variable "create_cur" {
  type        = bool
  default     = false
  description = "When true, creates an S3 bucket and CUR report definition. Use for management/payer accounts that do not yet have a CUR configured. Mutually exclusive with cur_bucket_name."
}

variable "cur_bucket_name" {
  type        = string
  default     = ""
  description = "Name of an existing S3 bucket containing CUR data. When set, the IAM role gets S3 read access to this bucket. Use for management/payer accounts with an existing CUR. Mutually exclusive with create_cur."

  validation {
    condition     = var.cur_bucket_name == "" || can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.cur_bucket_name))
    error_message = "Must be a valid S3 bucket name."
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# CUR Configuration (only when create_cur = true)
# ---------------------------------------------------------------------------------------------------------------------

variable "cur_report_name" {
  type        = string
  default     = "cloudzero-cur-hourly-csv"
  description = "Name for the CUR report definition."
}

variable "cur_s3_prefix" {
  type        = string
  default     = "cloudzero"
  description = "S3 key prefix for CUR report files."
}


variable "cur_bucket_name_prefix" {
  type        = string
  default     = "cz-cur"
  description = "Prefix for the auto-generated CUR S3 bucket name. A random suffix is appended."
}

variable "cur_bucket_lifecycle_days" {
  type        = number
  default     = null
  description = "Number of days before CUR objects expire. Set to null to disable lifecycle expiration."
}

variable "cur_bucket_force_destroy" {
  type        = bool
  default     = false
  description = "Allow Terraform to destroy the CUR S3 bucket even if it contains objects. Use with caution — billing data is not recoverable."
}

# ---------------------------------------------------------------------------------------------------------------------
# IAM Configuration
# ---------------------------------------------------------------------------------------------------------------------

variable "role_name" {
  type        = string
  default     = "cloudzero-access"
  description = "Name of the IAM role to create for CloudZero cross-account access."
}

variable "role_path" {
  type        = string
  default     = "/"
  description = "IAM role path. CloudFormation uses /cloudzero/ but the default here is / for backward compatibility with existing Terraform deployments."
}

variable "cloudzero_account_id" {
  type        = string
  default     = "061190967865"
  description = "The CloudZero AWS account ID that will assume the cross-account role. Override only if directed by CloudZero support."
}

variable "permissions_boundary" {
  type        = string
  default     = null
  description = "ARN of an IAM permissions boundary to attach to the CloudZero role."
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags to apply to all created AWS resources."
}

# ---------------------------------------------------------------------------------------------------------------------
# Feature Toggles
# ---------------------------------------------------------------------------------------------------------------------

variable "enable_activity_monitoring" {
  type        = bool
  default     = true
  description = "Attach the activity monitoring IAM policy (CloudTrail, health checks, service quotas, resource groups, tagging)."
}

variable "enable_container_insights" {
  type        = bool
  default     = true
  description = "Attach the Container Insights IAM policy (CloudWatch Logs for /aws/containerinsights/*)."
}

variable "enable_cloudwatch_metrics" {
  type        = bool
  default     = true
  description = "Attach the CloudWatch metrics IAM policy (autoscaling, cloudwatch describe/get/list)."
}

variable "enable_reserved_capacity" {
  type        = bool
  default     = true
  description = "Attach the reserved capacity IAM policy (EC2, RDS, DynamoDB, ElastiCache, OpenSearch, Redshift reserved instance descriptions)."
}

variable "enable_optimization_hub" {
  type        = bool
  default     = true
  description = "Attach the Cost Optimization Hub IAM policy."
}

variable "enable_cloudformation_access" {
  type        = bool
  default     = true
  description = "Attach the CloudFormation read-only IAM policy."
}

# ---------------------------------------------------------------------------------------------------------------------
# Extensibility
# ---------------------------------------------------------------------------------------------------------------------

variable "additional_managed_policy_arns" {
  type        = list(string)
  default     = []
  description = "Additional AWS managed policy ARNs to attach to the CloudZero role."
}
