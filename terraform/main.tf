provider "aws" {
  region = var.aws_region
}

locals {
  external_libs = "${var.deployment_staging}/ext-libs"
  lambda_functions = {
      "${var.aws_stage}-hello"       = "scripts/hello"
  }
  custom_lambda_layers = ["main"]
  pandas_lambda_layer_arn = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python312:1"
}

module "lambda_function" { 
  source = "./aws-lambda"
  for_each = local.lambda_functions
  function_name = each.key
  function_path = each.value
  timeout = 60
  deployment_staging   = var.deployment_staging
  layers = [local.pandas_lambda_layer_arn, module.lambda_layer["main"].arn]
  environment_variables = {
    "DERIBIT_CLIENT_ID": var.deribit_client_id,
    "DERIBIT_CLIENT_SECRET": var.deribit_client_secret,
    "DERIBIT_BUCKET_POSITIONS": "${var.aws_stage}-deribit-positions"
  }
  depends_on  = [module.lambda_layer]
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
  for_each = toset(local.custom_lambda_layers)
  poetry_group = each.value
  deployment_staging = var.deployment_staging
  layer_bucket_name = aws_s3_bucket.lambda_layers_ext_libs.id
  aws_stage = var.aws_stage
}
