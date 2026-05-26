variable "cloudzero_external_id" {
  type = string
  description = "The CloudZero provided External ID for your cross account access role (Your ID can be found on the CloudZero manual account connection page)"
}

variable "connectors_account_id" {
  type        = string
  default     = "931830253929"
  description = "Additional CloudZero AWS account ID that will assume the cross-account role. Override only if directed by CloudZero support."
}
