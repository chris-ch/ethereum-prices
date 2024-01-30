variable "aws_region" {
  type = string
}

variable "aws_stage" {
  type = string
}

variable "deribit_client_id" {
  type = string
}

variable "deribit_client_secret" {
  type = string
}

variable "deployment_staging" {
  type = string
  default = ".deploy"
}
