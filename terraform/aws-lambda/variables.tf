variable "function_path" {
  type = string
}

variable "function_name" {
  type = string
}

variable "environment_variables" {
  type = map(string)
}

variable "timeout" {
  type = number
}

variable "deployment_staging" {
  type = string
}

variable "layers" {
  type = set(string)
}

variable "handler" {
  type = string
}

variable "runtime" {
  type = string
}
