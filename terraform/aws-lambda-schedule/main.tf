resource "aws_cloudwatch_event_rule" "schedule_rule" {
  name                = var.name
  description         = var.description
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "scheduled_target_config" {
  rule      = aws_cloudwatch_event_rule.schedule_rule.name
  arn       = var.target_function.arn
  input     = var.payload
}

resource "aws_lambda_permission" "scheduled_lambda_allow_cloudwatch" {
  action        = "lambda:InvokeFunction"
  function_name = var.target_function.name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule_rule.arn
}
