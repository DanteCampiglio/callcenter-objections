data "aws_caller_identity" "current" {}

data "aws_secretsmanager_secret" "gitlab_token" {
  name = "${local.project_cfg["prefix"]}-${var.gitlab_token_secret_name}"
}

data "aws_secretsmanager_secret_version" "gitlab_token" {
  secret_id = data.aws_secretsmanager_secret.gitlab_token.id
}
