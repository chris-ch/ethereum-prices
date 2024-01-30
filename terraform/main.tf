provider "aws" {
  region = var.aws_region
}

locals {
  external_libs = "${var.deployment_staging}/ext-libs"
  lambda_functions = {
      "${var.aws_stage}-hello"       = "scripts/hello"
  }
  lambda_layers = ["arrow", "pandas"]
}

module "lambda_function" { 
  source = "./aws-lambda"
  for_each = local.lambda_functions
  function_name = each.key
  function_path = each.value
  timeout = 60
  deployment_staging   = var.deployment_staging
  layers = [module.lambda_layer["pandas"].arn]
  environment_variables = {
    "DERIBIT_CLIENT_ID": var.deribit_client_id,
    "DERIBIT_CLIENT_SECRET": var.deribit_client_secret,
    "DERIBIT_BUCKET_POSITIONS": "${var.aws_stage}-deribit-positions"
  }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "lambda_layers_ext_libs" {
  bucket = "${var.aws_stage}-lambda-layers-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.aws_stage
  }
}

module "lambda_layer" {
  source = "./aws-layer"
  for_each = toset(local.lambda_layers)
  poetry_group = each.value
  deployment_staging = var.deployment_staging
  layer_bucket_name = aws_s3_bucket.lambda_layers_ext_libs.id
  aws_stage = var.aws_stage
}
