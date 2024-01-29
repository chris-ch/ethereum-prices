provider "aws" {
  region = var.aws_region
}


locals {
  hello_lambda_dir_name       = "scripts/hello"

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
  environment_variables = {
    "DERIBIT_CLIENT_ID": var.deribit_client_id,
    "DERIBIT_CLIENT_SECRET": var.deribit_client_secret,
    "DERIBIT_BUCKET_POSITIONS": "${var.aws_stage}-deribit-positions"
  }
}
