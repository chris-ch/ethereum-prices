provider "aws" {
  region = var.aws_region
}

locals {
  external_libs = "${var.deployment_staging}/ext-libs"
  lambda_functions = {
      "hello" = {
          path = "src/lambdas/hello.py"
          handler = "lambdas.hello.handler"
          runtime = "python3.12"
          timeout = 60
          memory_size = 128
          environment_variables = {
            "DERIBIT_CLIENT_ID": var.deribit_client_id,
            "DERIBIT_CLIENT_SECRET": var.deribit_client_secret,
            "DERIBIT_BUCKET_POSITIONS": "${var.aws_stage}-deribit-positions"
          }
        },
      "aggregate-prices" = {
          path = "src/lambdas/aggregateprices.py"
          handler = "lambdas.aggregateprices.handler"
          runtime = "python3.12"
          timeout = 180
          memory_size = 256
          environment_variables = {
            "BUCKET_BINANCE_PRICES": aws_s3_bucket.store_binance_prices.bucket,
            "BINANCE_PRICES_UPDATE": "false",
            "SLACK_WEBHOOK_URL": var.slack_webhook_url
          }
        },
      "evaluate-options" = {
          path = "src/lambdas/evaluateoptions.py"
          handler = "lambdas.evaluateoptions.handler"
          runtime = "python3.12"
          timeout = 30
          memory_size = 256
          environment_variables = {
            "BUCKET_BINANCE_PRICES": aws_s3_bucket.store_binance_prices.bucket,
            "CUT_OFF_YEAR_MONTH": "202201",
            "SLACK_WEBHOOK_URL": var.slack_webhook_url
          }
        }
  }
  custom_lambda_layers = ["main"]
  pandas_lambda_layer_arn = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python312:1"

  lambda_schedules = {
      "evaluate-options-2-days" = {
          target_function = module.lambda_function["evaluate-options"]
          schedule_expression = "cron(15 * * * ? *)"
          payload = jsonencode({
            binance_symbol = "ETHUSDT"
            strikes_universe_size = 4
            target_period_hours = 48
          })
          description = "Schedule for options valuations"
      },
      "evaluate-options-3-days" = {
          target_function = module.lambda_function["evaluate-options"]
          schedule_expression = "cron(45 * * * ? *)"
          payload = jsonencode({
            binance_symbol = "ETHUSDT"
            strikes_universe_size = 4
            target_period_hours = 72
          })
          description = "Schedule for options valuations"
      }
  }
}

module "lambda_function" { 
  source = "./aws-lambda"
  for_each = local.lambda_functions
  function_name = "${var.aws_stage}-${each.key}"
  function_path = each.value.path
  handler = each.value.handler
  runtime = each.value.runtime
  timeout = each.value.timeout
  deployment_staging   = var.deployment_staging
  memory_size = each.value.memory_size
  layers = [local.pandas_lambda_layer_arn, module.lambda_layer["main"].arn]
  environment_variables = each.value.environment_variables
  depends_on  = [module.lambda_layer]
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "store_binance_prices" {
  bucket = "${var.aws_stage}-binance-prices-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.aws_stage
  }
}

resource "aws_s3_bucket" "store_unit_testing" {
  bucket = "${var.aws_stage}-unit-testing-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.aws_stage
  }
}

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

module "aws_lambda_schedule" {
  source = "./aws-lambda-schedule"
  for_each = local.lambda_schedules
  target_function = each.value.target_function
  schedule_expression = each.value.schedule_expression
  payload = each.value.payload
  description = each.value.description
  name = "${var.aws_stage}-${each.key}"
}
