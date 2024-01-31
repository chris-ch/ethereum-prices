
output "arn" {
  value = aws_lambda_layer_version.lambda_layer_ext_libs.arn
}

output "requirement_file" {
  value = local.requirement_file
}
