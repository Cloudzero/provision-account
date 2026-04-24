output "role_arn" {
  description = "ARN of the CloudZero cross-account IAM role."
  value       = aws_iam_role.cloudzero.arn
}

output "role_name" {
  description = "Name of the CloudZero cross-account IAM role."
  value       = aws_iam_role.cloudzero.name
}

output "role_id" {
  description = "Unique ID of the CloudZero cross-account IAM role."
  value       = aws_iam_role.cloudzero.unique_id
}

output "account_id" {
  description = "AWS account ID where the role was created."
  value       = data.aws_caller_identity.current.account_id
}

output "is_management_account" {
  description = "Whether this module was configured for a management/payer account."
  value       = local.is_management
}

output "cur_bucket_name" {
  description = "Name of the CUR S3 bucket (created or existing). Null for member accounts."
  value       = local.is_management ? local.cur_bucket : null
}

output "cur_bucket_arn" {
  description = "ARN of the created CUR S3 bucket. Null if the bucket was not created by this module."
  value       = var.create_cur ? aws_s3_bucket.cur[0].arn : null
}

output "cur_report_name" {
  description = "Name of the CUR report definition. Null if no CUR was created by this module."
  value       = var.create_cur ? aws_cur_report_definition.cloudzero[0].report_name : null
}
