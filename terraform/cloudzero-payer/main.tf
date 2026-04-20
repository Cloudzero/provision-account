locals {
  cz_account_id = "061190967865"
}

resource "aws_iam_role" "cloudzero" {
  name               = "cloudzero-access"
  path               = "/cloudzero/"
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
          "Sid" : "CZTier0BillingBucket20260420",
          "Effect" : "Allow",
          "Action" : [
            "s3:Get*",
            "s3:List*"
          ],
          "Resource" : [
            "arn:aws:s3:::${var.AWS_CUR_bucket}",
            "arn:aws:s3:::${var.AWS_CUR_bucket}/*"
          ]
        },
        {
          "Sid" : "CZTier0BillingDataAccess20260420",
          "Effect" : "Allow",
          "Action" : [
            "account:GetAccountInformation",
            "bcm-data-exports:Get*",
            "bcm-data-exports:List*",
            "billing:Get*",
            "ce:Describe*",
            "ce:Get*",
            "ce:List*",
            "consolidatedbilling:Get*",
            "consolidatedbilling:List*",
            "cur:Describe*",
            "cur:Get*",
            "cur:List*",
            "cur:Validate*",
            "freetier:Get*",
            "invoicing:Get*",
            "invoicing:List*",
            "mapcredits:List*",
            "payments:Get*",
            "payments:List*",
            "purchase-orders:Get*",
            "purchase-orders:List*",
            "purchase-orders:View*",
            "sustainability:Get*",
            "tax:Get*",
            "tax:List*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier0ReservedCapacity20260420",
          "Effect" : "Allow",
          "Action" : [
            "dynamodb:DescribeReserved*",
            "ec2:DescribeReserved*",
            "elasticache:DescribeReserved*",
            "es:DescribeReserved*",
            "rds:DescribeReserved*",
            "redshift:DescribeReserved*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier0SavingsPlans20260420",
          "Effect" : "Allow",
          "Action" : [
            "savingsplans:Describe*",
            "savingsplans:Get*",
            "savingsplans:List*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1Budgets20260420",
          "Effect" : "Allow",
          "Action" : [
            "budgets:Describe*",
            "budgets:View*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1BillingConductor20260420",
          "Effect" : "Allow",
          "Action" : [
            "billingconductor:Get*",
            "billingconductor:List*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1PricingAndForecasting20260420",
          "Effect" : "Allow",
          "Action" : [
            "bcm-pricing-calculator:Get*",
            "bcm-pricing-calculator:List*",
            "pricing:*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1OrganizationsAndTags20260420",
          "Effect" : "Allow",
          "Action" : [
            "account:ListRegions",
            "organizations:Describe*",
            "organizations:List*",
            "resource-explorer:List*",
            "resource-groups:Get*",
            "resource-groups:List*",
            "resource-groups:Search*",
            "tag:Describe*",
            "tag:Get*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1ComputeOptimizer20260420",
          "Effect" : "Allow",
          "Action" : [
            "compute-optimizer:Describe*",
            "compute-optimizer:Get*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1CostOptimizationHub20260420",
          "Effect" : "Allow",
          "Action" : [
            "cost-optimization-hub:Get*",
            "cost-optimization-hub:List*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1TrustedAdvisorAndHealth20260420",
          "Effect" : "Allow",
          "Action" : [
            "health:Describe*",
            "support:DescribeTrustedAdvisor*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier1ContainerInsightsLogs20260420",
          "Effect" : "Allow",
          "Action" : [
            "logs:Describe*",
            "logs:Filter*",
            "logs:Get*",
            "logs:List*",
            "logs:StartQuery",
            "logs:StopQuery"
          ],
          "Resource" : "arn:aws:logs:*:*:log-group:/aws/containerinsights/*"
        },
        {
          "Sid" : "CZTier1ContainerInsightsLogQuery20260420",
          "Effect" : "Allow",
          "Action" : [
            "logs:DescribeLogGroups",
            "logs:GetQueryResults"
          ],
          "Resource" : "arn:aws:logs:*:*:log-group:*"
        },
        {
          "Sid" : "CZTier2CloudTrail20260420",
          "Effect" : "Allow",
          "Action" : [
            "cloudtrail:Describe*",
            "cloudtrail:Get*",
            "cloudtrail:List*",
            "cloudtrail:LookupEvents"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier2ServiceQuotas20260420",
          "Effect" : "Allow",
          "Action" : [
            "servicequotas:Get*",
            "servicequotas:List*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier2CloudWatchMetrics20260420",
          "Effect" : "Allow",
          "Action" : [
            "autoscaling:Describe*",
            "cloudwatch:Describe*",
            "cloudwatch:Get*",
            "cloudwatch:List*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier2CloudFormation20260420",
          "Effect" : "Allow",
          "Action" : [
            "cloudformation:Describe*",
            "cloudformation:Get*",
            "cloudformation:List*"
          ],
          "Resource" : "*"
        },
        {
          "Sid" : "CZTier2SelfInspection20260420",
          "Effect" : "Allow",
          "Action" : [
            "iam:GetRole",
            "iam:GetRolePolicy",
            "iam:ListAttachedRolePolicies",
            "iam:ListRolePolicies",
            "iam:ListRoleTags",
            "iam:SimulatePrincipalPolicy"
          ],
          "Resource" : "arn:aws:iam::*:role/cloudzero/*"
        },
        {
          "Sid" : "CZTier2SelfInspectionPolicies20260420",
          "Effect" : "Allow",
          "Action" : [
            "iam:GetPolicy",
            "iam:GetPolicyVersion"
          ],
          "Resource" : "*"
        }
      ]
    })
}

resource "aws_iam_role_policy_attachment" "compute_optimizer_access" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/ComputeOptimizerReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "view_only_access" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"
}
