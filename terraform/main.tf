provider "aws" {
  region = var.aws_region
}

locals {
  external_libs = "${var.deployment_staging}/ext-libs"
  lambda_functions = {
      "${var.aws_stage}-hello"       = "scripts/hello"
  }
}

module "lambda_function" { 
  source = "./aws-lambda"
  for_each = local.lambda_functions
  function_name = each.key
  function_path = each.value
  timeout = 60
  deployment_staging   = var.deployment_staging
  environment_variables = {
    "DERIBIT_CLIENT_ID": var.deribit_client_id,
    "DERIBIT_CLIENT_SECRET": var.deribit_client_secret,
    "DERIBIT_BUCKET_POSITIONS": "${var.aws_stage}-deribit-positions"
  }
}

data "archive_file" "lambda_external_libs" {
  type        = "zip"
  output_path = "${var.deployment_staging}/lambda-external-libs.zip"
  source_dir = "${local.external_libs}"
  depends_on = [null_resource.sync_ext_libs]
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "lambda_layer" {
  bucket = "${var.aws_stage}-lambda-layer-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.aws_stage
  }
}

resource "null_resource" "sync_ext_libs" {
  triggers = {
    script_hash = sha256("${var.deployment_staging}/requirements.txt")
  }
  provisioner "local-exec" {
    command = "mkdir -p ${var.deployment_staging} && poetry export --format='requirements.txt' > ${var.deployment_staging}/requirements.txt && pip install --requirement ${var.deployment_staging}/requirements.txt --target ${var.deployment_staging}/ext-libs"
  }
}

resource "aws_s3_object" "lambda_layer_zip" {
  bucket     = aws_s3_bucket.lambda_layer.id
  key        = "external-libs.zip"
  source     = "${var.deployment_staging}/lambda-external-libs.zip"
  depends_on = [ data.archive_file.lambda_external_libs ]
}
