locals {
  lambda_main = "${path.cwd}/${var.function_path}"
  #lambda_lib_files_relative = fileset("${path.cwd}/src", "**.py")
  #lambda_lib_files = [for lambda_file in local.lambda_lib_files_relative : "${path.cwd}/src/${lambda_file}"]
  lambda_files_path = "${var.deployment_staging}/${var.function_name}"
}

resource "null_resource" "sync_deployment_files" {
  #for_each = local.lambda_files
  triggers = {
    timestamp = timestamp()
    #script_hash = sha256(each.value)
  }
  provisioner "local-exec" {
    command = <<EOT
      rm -fr ${local.lambda_files_path} \
      && mkdir -p ${local.lambda_files_path} \
      && cp -r ${path.cwd}/src/* ${local.lambda_files_path} \
      && find ${local.lambda_files_path} -type d -name "__pycache__" | xargs rm -rf \
      && cp ${local.lambda_main} ${local.lambda_files_path}/.
      EOT
  }
}

data "archive_file" "lambda_package" {
  type        = "zip"
  output_path = "${var.deployment_staging}/lambda-${var.function_name}.zip"
  source_dir = "${var.deployment_staging}/${var.function_name}"
  depends_on = [null_resource.sync_deployment_files]
}

resource "aws_lambda_function" "lambda_function" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = var.function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  timeout          = var.timeout
  memory_size = var.memory_size
  layers = var.layers
  environment {
    variables = var.environment_variables
  }
  depends_on = [
    data.archive_file.lambda_package
  ]
}

# IAM
data "aws_iam_policy_document" "assume_role_lambda" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda-exec-${var.function_name}"
  assume_role_policy = data.aws_iam_policy_document.assume_role_lambda.json
}

data "aws_iam_policy" "lambda_logs_policy" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy" "lambda_s3_policy" {
  arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda_logs_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = data.aws_iam_policy.lambda_logs_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_s3_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = data.aws_iam_policy.lambda_s3_policy.arn
}