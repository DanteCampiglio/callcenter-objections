locals {
  secret_value = jsondecode(data.aws_secretsmanager_secret_version.gitlab_token.secret_string)
}

locals {
  project_cfg = yamldecode(file("${path.module}/../../project.yaml"))
}

locals {
  model_cfg = yamldecode(file("${path.module}/../../src/pipelines/sagemaker/config/model.yaml"))
}

locals {
  lambda_trigger_name = var.image_name != "" ? var.image_name : "${local.project_cfg["prefix"]}-${local.project_cfg["model_approval_lambda"]}"
}
