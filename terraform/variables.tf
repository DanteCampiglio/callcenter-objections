variable "docker_tag" {
  type    = string
  default = "latest"
}

variable "image_name" {
  type    = string
  default = ""
}

variable "region" {
  type    = string
  default = "eu-central-1"
}

variable "gitlab_token_secret_name" {
  type    = string
  default = "monorepo"
}
