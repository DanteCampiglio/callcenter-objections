variable "project_prefix" {
  type    = string
  default = "contact-center"
}

variable "pipeline_name" {
  type    = string
  default = "contact-center"
}

variable "cost_center" {
  type    = string
  default = "CONTACT_CENTER"
}

variable "model_package_group_name" {
  type    = string
  default = "contact-center-models"
}

variable "lambda_repository_suffix" {
  type    = string
  default = "model-approval-trigger"
}

variable "docker_tag" {
  type    = string
  default = "latest"
}

variable "image_name" {
  type    = string
  default = ""
}

variable "lambda_image_uri" {
  # Provide a fully-qualified ECR image URI (e.g., 123456789012.dkr.ecr.eu-central-1.amazonaws.com/contact-center-dashboard:latest)
  # to bypass the automatic lookup of the most recent image in the managed repository.
  description = "Optional fully-qualified ECR image URI for the Lambda function. When provided, Terraform will skip looking up the latest image in the managed repository and use this URI directly."
  type        = string
  default     = null
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "gitlab_token_secret_name" {
  type    = string
  default = "monorepo"
}
