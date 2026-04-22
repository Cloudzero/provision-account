# ---------------------------------------------------------------------------------------------------------------------
# Data Sources
# ---------------------------------------------------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

locals {
  is_management = var.create_cur || var.cur_bucket_name != ""
  cur_bucket    = var.create_cur ? aws_s3_bucket.cur[0].id : var.cur_bucket_name

  # Managed policy ARNs that are actually attached — used by self-inspection statement
  attached_managed_policy_arns = concat(
    ["arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess"],
    ["arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"],
    var.enable_tier1_compute_optimizer ? ["arn:aws:iam::aws:policy/ComputeOptimizerReadOnlyAccess"] : [],
    var.enable_tier2_cloudwatch_metrics ? ["arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"] : [],
  )
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
# Inline Policy — Tiered structure matching policies/master_payer.json
#
# Tier 0: Cost and usage data ingestion (always enabled)
# Tier 1: Cost optimization signals (enabled by default, toggleable)
# Tier 2: Operational visibility (enabled by default, toggleable)
# ---------------------------------------------------------------------------------------------------------------------

data "aws_iam_policy_document" "cloudzero" {

  # ===== TIER 0: Cost and usage data ingestion =====

  # S3 CUR bucket access (management accounts only)
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

  # Billing data access (always enabled — core functionality)
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

  # Reserved capacity (always enabled — core)
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

  # Savings Plans (always enabled — core)
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

  dynamic "statement" {
    for_each = var.enable_tier1_budgets ? [1] : []
    content {
      sid    = "CZTier1Budgets20260420"
      effect = "Allow"
      actions = [
        "budgets:Describe*",
        "budgets:View*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier1_billing_conductor ? [1] : []
    content {
      sid    = "CZTier1BillingConductor20260420"
      effect = "Allow"
      actions = [
        "billingconductor:Get*",
        "billingconductor:List*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier1_pricing ? [1] : []
    content {
      sid    = "CZTier1PricingAndForecasting20260420"
      effect = "Allow"
      actions = [
        "bcm-pricing-calculator:Get*",
        "bcm-pricing-calculator:List*",
        "pricing:*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier1_organizations_and_tags ? [1] : []
    content {
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
  }

  dynamic "statement" {
    for_each = var.enable_tier1_compute_optimizer ? [1] : []
    content {
      sid    = "CZTier1ComputeOptimizer20260420"
      effect = "Allow"
      actions = [
        "compute-optimizer:Describe*",
        "compute-optimizer:Get*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier1_cost_optimization_hub ? [1] : []
    content {
      sid    = "CZTier1CostOptimizationHub20260420"
      effect = "Allow"
      actions = [
        "cost-optimization-hub:Get*",
        "cost-optimization-hub:List*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier1_trusted_advisor ? [1] : []
    content {
      sid    = "CZTier1TrustedAdvisorAndHealth20260420"
      effect = "Allow"
      actions = [
        "health:Describe*",
        "support:DescribeTrustedAdvisor*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier1_container_insights ? [1] : []
    content {
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
  }

  dynamic "statement" {
    for_each = var.enable_tier1_container_insights ? [1] : []
    content {
      sid    = "CZTier1ContainerInsightsLogQuery20260420"
      effect = "Allow"
      actions = [
        "logs:DescribeLogGroups",
        "logs:GetQueryResults",
      ]
      resources = ["arn:aws:logs:*:*:log-group:*"]
    }
  }

  # ===== TIER 2: Operational visibility =====

  dynamic "statement" {
    for_each = var.enable_tier2_cloudtrail ? [1] : []
    content {
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
  }

  dynamic "statement" {
    for_each = var.enable_tier2_service_quotas ? [1] : []
    content {
      sid    = "CZTier2ServiceQuotas20260420"
      effect = "Allow"
      actions = [
        "servicequotas:Get*",
        "servicequotas:List*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier2_cloudwatch_metrics ? [1] : []
    content {
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
  }

  dynamic "statement" {
    for_each = var.enable_tier2_cloudformation ? [1] : []
    content {
      sid    = "CZTier2CloudFormation20260420"
      effect = "Allow"
      actions = [
        "cloudformation:Describe*",
        "cloudformation:Get*",
        "cloudformation:List*",
      ]
      resources = ["*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier2_self_inspection ? [1] : []
    content {
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
      resources = ["arn:aws:iam::*:role/cloudzero/*"]
    }
  }

  dynamic "statement" {
    for_each = var.enable_tier2_self_inspection ? [1] : []
    content {
      sid    = "CZTier2SelfInspectionPolicies20260420"
      effect = "Allow"
      actions = [
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
      ]
      resources = local.attached_managed_policy_arns
    }
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

# Tier 0: always attached — core CloudZero functionality
resource "aws_iam_role_policy_attachment" "billing_read_only" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "view_only" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"
}

# Conditional: controlled by feature toggles
resource "aws_iam_role_policy_attachment" "compute_optimizer" {
  count      = var.enable_tier1_compute_optimizer ? 1 : 0
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/ComputeOptimizerReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_read_only" {
  count      = var.enable_tier2_cloudwatch_metrics ? 1 : 0
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
