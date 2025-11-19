locals {
  project_cfg = {
    prefix              = var.project_prefix
    pipeline_name       = var.pipeline_name
    cost_center         = var.cost_center
    model_approval_name = var.lambda_repository_suffix
  }

  model_cfg = {
    register = {
      name = var.model_package_group_name
    }
  }

  lambda_trigger_name = var.image_name != "" ? var.image_name : "${local.project_cfg["prefix"]}-${local.project_cfg["model_approval_name"]}"

  use_latest_ecr_image = var.lambda_image_uri == null || trim(var.lambda_image_uri) == ""
}
