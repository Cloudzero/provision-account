locals {
  cz_account_id = "061190967865"
}

resource "aws_iam_role" "cloudzero" {
  name               = "cloudzero-access"
  path               = "/"
  assume_role_policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Sid" : "",
          "Effect" : "Allow",
          "Principal" : {
            "AWS" : "arn:aws:iam::${local.cz_account_id}:root"
          },
          "Action" : "sts:AssumeRole",
          "Condition" : {
            "StringEquals" : {
              "sts:ExternalId" : var.cloudzero_external_id
            }
          }
        }
      ]
    })
}

resource "aws_iam_role_policy" "CloudZero" {
  name   = "cloudzero-access-policy"
  role   = aws_iam_role.cloudzero.id
  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Sid" : "AccessCURDataBucket1",
          "Effect" : "Allow",
          "Action" : [
            "S3:get*",
            "S3:list*"
          ],
          "Resource" : [
            "arn:aws:s3:::${var.AWS_CUR_bucket}",
            "arn:aws:s3:::${var.AWS_CUR_bucket}/*"
          ]
        },
        {
          "Sid": "CZCostMonitoring20230119",
          "Effect": "Allow",
          "Action": [
            "account:GetAccountInformation",
            "billing:Get*",
            "budgets:Describe*",
            "budgets:View*",
            "ce:Describe*",
            "ce:Get*",
            "ce:List*",
            "consolidatedbilling:Get*",
            "consolidatedbilling:List*",
            "cur:Describe*",
            "cur:Get*",
            "cur:Validate*",
            "cur:List*",
            "freetier:Get*",
            "invoicing:Get*",
            "invoicing:List*",
            "organizations:Describe*",
            "organizations:List*",
            "payments:Get*",
            "payments:List*",
            "pricing:*",
            "tax:Get*",
            "tax:List*"
          ],
          "Resource": "*"
        },
        {
          "Sid": "CZActivityMonitoring20210423",
          "Effect": "Allow",
          "Action": [
            "cloudtrail:Get*",
            "cloudtrail:List*",
            "cloudtrail:Describe*",
            "health:Describe*",
            "support:DescribeTrustedAdvisor*",
            "servicequotas:Get*",
            "servicequotas:List*",
            "resource-groups:Get*",
            "resource-groups:List*",
            "resource-groups:Search*",
            "cloudformation:DescribeStacks",
            "cloudformation:ListStackResources",
            "tag:Get*",
            "tag:Describe*",
            "resource-explorer:List*",
            "account:ListRegions"
          ],
          "Resource": "*"
        },
        {
          "Sid": "CZReservedCapacity20190912",
          "Effect": "Allow",
          "Action": [
            "dynamodb:DescribeReserved*",
            "ec2:DescribeReserved*",
            "elasticache:DescribeReserved*",
            "es:DescribeReserved*",
            "rds:DescribeReserved*",
            "redshift:DescribeReserved*"
          ],
          "Resource": "*"
        },
        {
          "Sid": "CloudZeroContainerInsightsAccess20210423",
          "Effect": "Allow",
          "Action": [
            "logs:List*",
            "logs:Describe*",
            "logs:StartQuery",
            "logs:StopQuery",
            "logs:Filter*",
            "logs:Get*"
          ],
          "Resource": "arn:aws:logs:*:*:log-group:/aws/containerinsights/*"
        },
        {
          "Sid": "CloudZeroCloudWatchContainerLogStreamAccess20210906",
          "Effect": "Allow",
          "Action": [
            "logs:GetQueryResults",
            "logs:DescribeLogGroups"
          ],
          "Resource": "arn:aws:logs:*:*:log-group::log-stream:*"
        },
        {
          "Sid": "CloudZeroCloudWatchMetricsAccess20210423",
          "Effect": "Allow",
          "Action": [
            "autoscaling:Describe*",
            "cloudwatch:Describe*",
            "cloudwatch:Get*",
            "cloudwatch:List*"
          ],
          "Resource": "*"
        }
      ]
    })
}

resource "aws_iam_role_policy_attachment" "security_audit_access" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/SecurityAudit"
}

resource "aws_iam_role_policy_attachment" "view_only_access" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"
}