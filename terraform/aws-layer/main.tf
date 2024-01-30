
resource "null_resource" "sync_ext_libs" {
  triggers = {
    timestamp = timestamp()
    #script_hash = sha256("${var.deployment_staging}/requirements-${var.poetry_group}.txt")
  }
  provisioner "local-exec" {
    command = <<EOT
    rm -fr ${var.deployment_staging}/ext-libs-${var.poetry_group} && \
    mkdir -p ${var.deployment_staging}/ext-libs-${var.poetry_group} && \
    poetry export --only ${var.poetry_group} --format='requirements.txt' > ${var.deployment_staging}/requirements-${var.poetry_group}.txt && \
    pip install --requirement ${var.deployment_staging}/requirements-${var.poetry_group}.txt --target ${var.deployment_staging}/ext-libs-${var.poetry_group}
    EOT
  }
}

data "archive_file" "lambda_external_libs" {
  type        = "zip"
  source_dir = "${var.deployment_staging}/ext-libs-${var.poetry_group}"
  output_path = "${var.deployment_staging}/lambda-layer-${var.poetry_group}.zip"
  depends_on = [null_resource.sync_ext_libs]
}

resource "aws_s3_object" "lambda_layer_ext_libs_zip" {
  bucket     = var.layer_bucket_name
  key        = "layer-${var.aws_stage}-${var.poetry_group}.zip"
  source     = "${var.deployment_staging}/lambda-layer-${var.poetry_group}.zip"
  depends_on = [ data.archive_file.lambda_external_libs ]
}

resource "aws_lambda_layer_version" "lambda_layer_ext_libs" {
  s3_bucket           = var.layer_bucket_name
  s3_key              = aws_s3_object.lambda_layer_ext_libs_zip.key
  layer_name          = "layer-${var.aws_stage}-${var.poetry_group}"
  compatible_runtimes = ["python3.12"]
  skip_destroy        = false
  depends_on          = [aws_s3_object.lambda_layer_ext_libs_zip]
}
