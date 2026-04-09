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
# Inline Policy — sourced from policies/master_payer.json (canonical Sids and actions)
# ---------------------------------------------------------------------------------------------------------------------

data "aws_iam_policy_document" "cloudzero" {
  # S3 CUR bucket access (management accounts only)
  dynamic "statement" {
    for_each = local.is_management ? [1] : []
    content {
      sid    = "AccessMasterPayerBillingBucket"
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

  # Cost monitoring (always enabled — core functionality)
  statement {
    sid    = "CZCostMonitoring20240422"
    effect = "Allow"
    actions = [
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
      "tax:List*",
    ]
    resources = ["*"]
  }

  # Activity monitoring
  dynamic "statement" {
    for_each = var.enable_activity_monitoring ? [1] : []
    content {
      sid    = "CZActivityMonitoring20210423"
      effect = "Allow"
      actions = [
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
        "tag:Get*",
        "tag:Describe*",
        "resource-explorer:List*",
        "account:ListRegions",
      ]
      resources = ["*"]
    }
  }

  # Reserved capacity
  dynamic "statement" {
    for_each = var.enable_reserved_capacity ? [1] : []
    content {
      sid    = "CZReservedCapacity20190912"
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
  }

  # Container Insights — CloudWatch Logs access
  dynamic "statement" {
    for_each = var.enable_container_insights ? [1] : []
    content {
      sid    = "CloudZeroContainerInsightsAccess20210423"
      effect = "Allow"
      actions = [
        "logs:List*",
        "logs:Describe*",
        "logs:StartQuery",
        "logs:StopQuery",
        "logs:Filter*",
        "logs:Get*",
      ]
      resources = ["arn:aws:logs:*:*:log-group:/aws/containerinsights/*"]
    }
  }

  # Container Insights — log stream access
  dynamic "statement" {
    for_each = var.enable_container_insights ? [1] : []
    content {
      sid    = "CloudZeroCloudWatchContainerLogStreamAccess20210906"
      effect = "Allow"
      actions = [
        "logs:GetQueryResults",
        "logs:DescribeLogGroups",
      ]
      resources = ["arn:aws:logs:*:*:log-group::log-stream:*"]
    }
  }

  # CloudWatch metrics
  dynamic "statement" {
    for_each = var.enable_cloudwatch_metrics ? [1] : []
    content {
      sid    = "CloudZeroCloudWatchMetricsAccess20210423"
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

  # Cost Optimization Hub
  dynamic "statement" {
    for_each = var.enable_optimization_hub ? [1] : []
    content {
      sid    = "ReadOnlyOptimizationHub20251103"
      effect = "Allow"
      actions = [
        "cost-optimization-hub:GetRecommendation",
        "cost-optimization-hub:ListRecommendations",
      ]
      resources = ["*"]
    }
  }

  # CloudFormation read access
  dynamic "statement" {
    for_each = var.enable_cloudformation_access ? [1] : []
    content {
      sid    = "CloudFormationAccess20251103"
      effect = "Allow"
      actions = [
        "cloudformation:Describe*",
        "cloudformation:Get*",
        "cloudformation:List*",
      ]
      resources = ["*"]
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

resource "aws_iam_role_policy_attachment" "compute_optimizer" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/ComputeOptimizerReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "view_only" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/job-function/ViewOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "billing_read_only" {
  role       = aws_iam_role.cloudzero.name
  policy_arn = "arn:aws:iam::aws:policy/AWSBillingReadOnlyAccess"
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
# the manual UI step. This requires:
#   1. terraform-provider-cloudzero published to the Terraform Registry
#   2. Public API endpoints: GET /accounts/v1/aws/info, POST/GET/PUT/DELETE /accounts/v1/aws
#
# resource "cloudzero_aws_account" "this" {
#   account_id   = data.aws_caller_identity.current.account_id
#   role_arn     = aws_iam_role.cloudzero.arn
#   bucket_arn   = local.is_management ? "arn:aws:s3:::${local.cur_bucket}" : null
#   account_name = var.account_name
# }
#
# At that point, the external_id variable can also be replaced by:
#
# data "cloudzero_aws_account_info" "this" {}
#
# ...which fetches the external ID and IAM policies directly from the
# CloudZero API, removing the need for manual copy-paste from the UI.
