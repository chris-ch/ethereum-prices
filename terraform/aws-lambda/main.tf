locals {
  lambda_main = "${path.cwd}/${var.function_path}/lambda.py"
  lambda_lib_files_relative = fileset("${path.cwd}/src", "*.py")
  lambda_lib_files = [for lambda_file in local.lambda_lib_files_relative : "${path.cwd}/src/${lambda_file}"]
  lambda_files = toset(concat(local.lambda_lib_files, [local.lambda_main]))
}

resource "null_resource" "sync_deployment_files" {
  for_each = local.lambda_files
  triggers = {
    script_hash = sha256(each.value)
  }
  provisioner "local-exec" {
    command = "rm -f ${var.deployment_staging}/${var.function_name}/${basename(each.value)} && mkdir -p ${var.deployment_staging}/${var.function_name} && cp ${each.value} ${var.deployment_staging}/${var.function_name}/${basename(each.value)}"
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
  handler          = "lambda.handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  timeout          = var.timeout
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