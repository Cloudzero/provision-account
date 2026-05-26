variable "cloudzero_external_id" {
  type = string
  description = "The CloudZero provided External ID for your cross account access role (Your ID can be found on the CloudZero manual account connection page)"
}

variable "AWS_CUR_bucket" {
  type = string
  description = "The S3 bucket where your AWS CUR is stored. Please ensure you have configured your CUR according to these instructions https://docs.cloudzero.com/docs/validate-your-cost-and-usage-report"
}

variable "connectors_account_id" {
  type        = string
  default     = "931830253929"
  description = "Additional CloudZero AWS account ID that will assume the cross-account role. Override only if directed by CloudZero support."
}
