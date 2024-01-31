variable "aws_region" {
  type = string
}

variable "aws_stage" {
  type = string
}

variable "deribit_client_id" {
  type = string
  default = "TBD"
}

variable "deribit_client_secret" {
  type = string
  default = "TBD"
}

variable "deployment_staging" {
  type = string
  default = ".deploy"
}
