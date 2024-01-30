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

# resource "null_resource" "project_lib_" {
# 	  triggers = {
#       script_hash = sha256(var.exe_path)
# 	  }
	
# 	  provisioner "local-exec" {
# 	    command = <<EOF
# 	    yarn config set no-progress
# 	    yarn
# 	    mkdir -p nodejs
# 	    cp -r node_modules nodejs/
# 	    rm -r node_modules
# 	    EOF
	

# 	    working_dir = "${path.module}/${var.code_location}"
# 	  }
# }
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "lambda_layers" {
  bucket = "${var.aws_stage}-lambda-layers-${data.aws_caller_identity.current.account_id}"

  tags = {
    Environment = var.aws_stage
  }
}

# resource "aws_s3_object" "layer_project_lib" {
#   bucket = aws_s3_bucket.lambda_layers
# 	  key    = "${var.aws_stage}-project-lib"
# 	  source = data.archive_file.main.output_path
# 	  etag   = data.archive_file.main.output_base64sha256

# 	  depends_on = [
# 	    data.archive_file.main,
# 	    null_resource.main,
# 	  ]
# }
