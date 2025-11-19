# -------------------------------
# ECR Repository for Lambda function
# -------------------------------
resource "aws_ecr_repository" "model_approval_lambda" {
  name                 = local.lambda_trigger_name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Get the latest image from ECR when no explicit URI is provided
data "aws_ecr_image" "model_approval_lambda" {
  count           = local.use_latest_ecr_image ? 1 : 0
  repository_name = aws_ecr_repository.model_approval_lambda.name
  most_recent     = true
}

resource "aws_cloudwatch_event_rule" "model_deploy_event_rule" {
  name        = "${local.project_cfg["prefix"]}-${local.project_cfg["pipeline_name"]}-model-approval"
  description = "Rule to trigger a deployment when SageMaker Model is Approved."

  event_pattern = jsonencode({
    source        = ["aws.sagemaker"]
    "detail-type" = ["SageMaker Model Package State Change"]
    detail = {
      ModelPackageGroupName = [local.model_cfg["register"]["name"]]
      ModelApprovalStatus   = ["Approved"]
    }
  })

  state = "ENABLED"

  # TEMPORARY: Ignore tags until SA-DSS user has events:TagResource permission
  # Once permission is granted:
  # 1. Request permission: events:TagResource, events:UntagResource, events:ListTagsForResource
  # 2. Delete this entire lifecycle block
  # 3. Event Rule will then be tagged via provider default_tags
  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

resource "aws_cloudwatch_event_target" "model_deploy_event_target" {
  rule      = aws_cloudwatch_event_rule.model_deploy_event_rule.name
  target_id = "${local.project_cfg["prefix"]}-${local.project_cfg["pipeline_name"]}-deploy"
  arn       = aws_lambda_function.model_approval_lambda.arn
}

resource "aws_lambda_permission" "permission_for_model_deploy_events_to_invoke_lambda" {
  statement_id  = "AllowExecutionFromCloudWatchModelDeployEvents"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.model_approval_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.model_deploy_event_rule.arn
}

resource "aws_lambda_function" "model_approval_lambda" {
  function_name = "${local.project_cfg["prefix"]}-${local.project_cfg["pipeline_name"]}-gl-trigger"
  description   = "To trigger the GitHub Workflow"
  package_type  = "Image"
  image_uri     = local.use_latest_ecr_image ? data.aws_ecr_image.model_approval_lambda[0].image_uri : var.lambda_image_uri
  role          = aws_iam_role.lambda_execution_role.arn
  timeout       = 900
  architectures = ["arm64"]

  environment {
    variables = {
      GitlabTokenSecretName = "${local.project_cfg["prefix"]}-${var.gitlab_token_secret_name}"
      Region                = var.region
    }
  }
  tags = {
    Application   = upper("${local.project_cfg["prefix"]}")
    "Cost Center" = "${local.project_cfg["cost_center"]}"
  }
}
