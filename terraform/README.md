# CloudZero Account Provisioning Terraform Templates for AWS

## About
These templates provide CloudZero with the necessary access permissions to analyze your cloud 
environment and guide you to optimize your cloud spend. 

To learn more about CloudZero, visit [CloudZero.com](cloudzero.com) or start by creating an account
at https://app.cloudzero.com and activating a free 30 day trial. Our online documentation is 
available at [docs.cloudzero.com](https://docs.cloudzero.com/docs/getting-started)

## Usage
These templates are intended for advanced users who have existing familiarity with Terraform. 

There are two templates available, use the correct one for the type of account you are connecting.
At a minimum you must connect your AWS Management account for CloudZero to function. In addition, to
provide additional insight into AWS Infrastructure, EKS or Kubernetes spend beyond the data is only
present in the AWS cost and usage data, you must connect the accounts you wish to monitor as resource
accounts.
 * For AWS Management (also called payer) accounts, use `cloudzero_payer_role.tf` 
 * For AWS Resource (or child) accounts, use `cloudzero_resource_role.tf`

### Pre-requisites for Connecting your AWS Accounts
 * Before connection ensure you have made note of the CloudZero provided External ID for your account (available from
the [CloudZero Manual Account Connection Page](https://app.cloudzero.com/organization/onboard-accounts/connect?cztabs.connect-accounts=manual))

 * To connect your AWS management account please first configure an [AWS Cost and Usage Report](https://docs.aws.amazon.com/cur/latest/userguide/cur-create.html)
and make note of the S3 bucket where the AWS CUR is being stored. 

## Getting Support
If you are unsure  how to run these templates, or would like to simply provision your accounts as quickly as possible,
consider running our automated CloudFormation based connection process via the CloudZero Web Application

If you have questions or want to report an issue with this template, feel free to open an issue or write to us at support@cloudzero.com
