# ---------------------------------------------------------------------------------------------------------------------
# CUR Setup (management accounts only, when create_cur = true)
# ---------------------------------------------------------------------------------------------------------------------
# Note: aws_cur_report_definition requires the AWS provider to target us-east-1.
# If your default provider targets a different region, use a provider alias:
#
#   provider "aws" {
#     alias  = "us_east_1"
#     region = "us-east-1"
#   }
#
#   module "cloudzero" {
#     source = "..."
#     providers = { aws = aws.us_east_1 }
#   }
# ---------------------------------------------------------------------------------------------------------------------

data "aws_region" "current" {}

resource "random_id" "cur_bucket_suffix" {
  count       = var.create_cur ? 1 : 0
  byte_length = 4
}

resource "aws_s3_bucket" "cur" {
  count         = var.create_cur ? 1 : 0
  bucket        = "${var.cur_bucket_name_prefix}-${random_id.cur_bucket_suffix[0].hex}"
  force_destroy = var.cur_bucket_force_destroy
  tags          = var.tags
}

resource "aws_s3_bucket_public_access_block" "cur" {
  count                   = var.create_cur ? 1 : 0
  bucket                  = aws_s3_bucket.cur[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "cur" {
  count  = var.create_cur && var.cur_bucket_lifecycle_days != null ? 1 : 0
  bucket = aws_s3_bucket.cur[0].id

  rule {
    id     = "expire-cur-data"
    status = "Enabled"

    expiration {
      days = var.cur_bucket_lifecycle_days
    }
  }
}

# Bucket policy granting the AWS billing reports service write access
data "aws_iam_policy_document" "cur_bucket" {
  count = var.create_cur ? 1 : 0

  statement {
    sid    = "AllowBillingReportsAccess"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["billingreports.amazonaws.com"]
    }

    actions = [
      "s3:GetBucketAcl",
      "s3:GetBucketPolicy",
    ]

    resources = [aws_s3_bucket.cur[0].arn]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }

  statement {
    sid    = "AllowBillingReportsPut"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["billingreports.amazonaws.com"]
    }

    actions = ["s3:PutObject"]

    resources = ["${aws_s3_bucket.cur[0].arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "cur" {
  count  = var.create_cur ? 1 : 0
  bucket = aws_s3_bucket.cur[0].id
  policy = data.aws_iam_policy_document.cur_bucket[0].json
}

resource "aws_cur_report_definition" "cloudzero" {
  count = var.create_cur ? 1 : 0

  report_name                = var.cur_report_name
  time_unit                  = "HOURLY"
  format                     = "textORcsv"
  compression                = "GZIP"
  additional_schema_elements = ["RESOURCES"]
  s3_bucket                  = aws_s3_bucket.cur[0].id
  s3_region                  = data.aws_region.current.name
  s3_prefix                  = var.cur_s3_prefix
  report_versioning          = "CREATE_NEW_REPORT"
  refresh_closed_reports     = true

  depends_on = [aws_s3_bucket_policy.cur]

  lifecycle {
    precondition {
      condition     = data.aws_region.current.name == "us-east-1"
      error_message = "CUR report definitions can only be created in us-east-1. Configure the AWS provider for this module to target us-east-1."
    }
  }
}
