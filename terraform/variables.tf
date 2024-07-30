variable "s3_bucket_states" {
    sensitive = true
}

variable "aws_region" {
  type = string
}

variable "aws_stage" {
  type = string
}

variable "deribit_client_id" {
  type = string
  default = ""
}

variable "deribit_client_secret" {
  type = string
  default = ""
}

variable "deployment_staging" {
  type = string
  default = ".deploy"
}

variable "slack_webhook_url" {
  type = string
  default = ""
}
