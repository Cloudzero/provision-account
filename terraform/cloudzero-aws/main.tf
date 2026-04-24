# ---------------------------------------------------------------------------------------------------------------------
# Data Sources
# ---------------------------------------------------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

locals {
  is_management = var.create_cur || var.cur_bucket_name != ""
  cur_bucket    = var.create_cur ? aws_s3_bucket.cur[0].id : var.cur_bucket_name
}

# ---------------------------------------------------------------------------------------------------------------------
# Cross-Account IAM Role
# ---------------------------------------------------------------------------------------------------------------------

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.cloudzero_account_id}:root"]
    }

    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [var.external_id]
    }
  }
}

resource "aws_iam_role" "cloudzero" {
  name                 = var.role_name
  path                 = var.role_path
  assume_role_policy   = data.aws_iam_policy_document.assume_role.json
  permissions_boundary = var.permissions_boundary
  tags                 = var.tags

  lifecycle {
    precondition {
      condition     = !(var.create_cur && var.cur_bucket_name != "")
      error_message = "create_cur and cur_bucket_name are mutually exclusive. Set create_cur = true to create a new CUR bucket, OR set cur_bucket_name to use an existing bucket."
    }
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# Inline Policy — matches policies/master_payer.json
#
# Tier 0: Cost and usage data ingestion
# Tier 1: Cost optimization signals
# Tier 2: Operational visibility
# ---------------------------------------------------------------------------------------------------------------------

data "aws_iam_policy_document" "cloudzero" {

  # ===== TIER 0: Cost and usage data ingestion =====

  dynamic "statement" {
    for_each = local.is_management ? [1] : []
    content {
      sid    = "CZTier0BillingBucket20260420"
      effect = "Allow"
      actions = [
        "s3:Get*",
        "s3:List*",
      ]
      resources = [
        "arn:aws:s3:::${local.cur_bucket}",
        "arn:aws:s3:::${local.cur_bucket}/*",
      ]
    }
  }

  statement {
    sid    = "CZTier0BillingDataAccess20260420"
    effect = "Allow"
    actions = [
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
      "tax:List*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier0ReservedCapacity20260420"
    effect = "Allow"
    actions = [
      "dynamodb:DescribeReserved*",
      "ec2:DescribeReserved*",
      "elasticache:DescribeReserved*",
      "es:DescribeReserved*",
      "rds:DescribeReserved*",
      "redshift:DescribeReserved*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier0SavingsPlans20260420"
    effect = "Allow"
    actions = [
      "savingsplans:Describe*",
      "savingsplans:List*",
    ]
    resources = ["*"]
  }

  # ===== TIER 1: Cost optimization signals =====

  statement {
    sid    = "CZTier1Budgets20260420"
    effect = "Allow"
    actions = [
      "budgets:Describe*",
      "budgets:View*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier1BillingConductor20260420"
    effect = "Allow"
    actions = [
      "billingconductor:Get*",
      "billingconductor:List*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier1PricingAndForecasting20260420"
    effect = "Allow"
    actions = [
      "bcm-pricing-calculator:Get*",
      "bcm-pricing-calculator:List*",
      "pricing:*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier1OrganizationsAndTags20260420"
    effect = "Allow"
    actions = [
      "account:ListRegions",
      "organizations:Describe*",
      "organizations:List*",
      "resource-explorer:List*",
      "resource-groups:Get*",
      "resource-groups:List*",
      "resource-groups:Search*",
      "tag:Describe*",
      "tag:Get*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier1ComputeOptimizer20260420"
    effect = "Allow"
    actions = [
      "compute-optimizer:Describe*",
      "compute-optimizer:Get*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier1CostOptimizationHub20260420"
    effect = "Allow"
    actions = [
      "cost-optimization-hub:Get*",
      "cost-optimization-hub:List*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier1TrustedAdvisorAndHealth20260420"
    effect = "Allow"
    actions = [
      "health:Describe*",
      "support:DescribeTrustedAdvisor*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier1ContainerInsightsLogs20260420"
    effect = "Allow"
    actions = [
      "logs:Describe*",
      "logs:Filter*",
      "logs:Get*",
      "logs:List*",
      "logs:StartQuery",
      "logs:StopQuery",
    ]
    resources = ["arn:aws:logs:*:*:log-group:/aws/containerinsights/*"]
  }

  statement {
    sid    = "CZTier1ContainerInsightsLogQuery20260420"
    effect = "Allow"
    actions = [
      "logs:DescribeLogGroups",
      "logs:GetQueryResults",
    ]
    resources = ["arn:aws:logs:*:*:log-group:*"]
  }

  # ===== TIER 2: Operational visibility =====

  statement {
    sid    = "CZTier2CloudTrail20260420"
    effect = "Allow"
    actions = [
      "cloudtrail:Describe*",
      "cloudtrail:Get*",
      "cloudtrail:List*",
      "cloudtrail:LookupEvents",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier2ServiceQuotas20260420"
    effect = "Allow"
    actions = [
      "servicequotas:Get*",
      "servicequotas:List*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier2CloudWatchMetrics20260420"
    effect = "Allow"
    actions = [
      "autoscaling:Describe*",
      "cloudwatch:Describe*",
      "cloudwatch:Get*",
      "cloudwatch:List*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier2CloudFormation20260420"
    effect = "Allow"
    actions = [
      "cloudformation:Describe*",
      "cloudformation:Get*",
      "cloudformation:List*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CZTier2SelfInspection20260420"
    effect = "Allow"
    actions = [
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:ListRolePolicies",
      "iam:ListRoleTags",
      "iam:SimulatePrincipalPolicy",
    ]
    resources = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role${var.role_path}*"]
  }

  statement {
    sid    = "CZTier2SelfInspectionPolicies20260420"
    effect = "Allow"
    actions = [
      "iam:GetPolicy",
      "iam:GetPolicyVersion",
    ]
    resources = [
      "arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess",
      "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
      "arn:aws:iam::aws:policy/ComputeOptimizerReadOnlyAccess",
      "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess",
    ]
  }
}

resource "aws_iam_role_policy" "cloudzero" {
  name   = "cloudzero-access-policy"
  role   = aws_iam_role.cloudzero.id
  policy = data.aws_iam_policy_document.cloudzero.json
}

# ---------------------------------------------------------------------------------------------------------------------
# Managed Policy Attachments
# ---------------------------------------------------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "billing_read_only" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "view_only" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "compute_optimizer" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/ComputeOptimizerReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_read_only" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "additional" {
  for_each   = toset(var.additional_managed_policy_arns)
  role       = aws_iam_role.cloudzero.name
  policy_arn = each.value
}

# ---------------------------------------------------------------------------------------------------------------------
# CloudZero Account Registration (Future)
# ---------------------------------------------------------------------------------------------------------------------
# When the CloudZero Terraform provider is available, the following resource
# will automatically register this AWS account with CloudZero — eliminating
# the manual UI step.
#
# resource "cloudzero_aws_account" "this" {
#   account_id   = data.aws_caller_identity.current.account_id
#   role_arn     = aws_iam_role.cloudzero.arn
#   bucket_arn   = local.is_management ? "arn:aws:s3:::${local.cur_bucket}" : null
#   account_name = var.account_name
# }
