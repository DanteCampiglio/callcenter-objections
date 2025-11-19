# -------------------------------
# IAM Role for Lambda Execution
# -------------------------------
# This role allows the model approval Lambda function to:
# - Execute and write logs to CloudWatch
# - Access GitLab token from Secrets Manager
# - Read SageMaker model package and processing job details
# It follows AWS best practices for least-privilege access

resource "aws_iam_role" "lambda_execution_role" {
  name        = "${local.project_cfg["prefix"]}-${local.project_cfg["pipeline_name"]}-lambda-exec"
  description = "Execution role for model approval Lambda function with least-privilege access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Application   = upper("${local.project_cfg["prefix"]}")
    "Cost Center" = "${local.project_cfg["cost_center"]}"
  }
}

# Attach AWS managed policy for basic Lambda execution (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for Secrets Manager access (GitLab token)
resource "aws_iam_role_policy" "lambda_secrets_access" {
  name = "${local.project_cfg["prefix"]}-${local.project_cfg["pipeline_name"]}-secrets"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = data.aws_secretsmanager_secret.gitlab_token.arn
      }
    ]
  })
}

# Custom policy for SageMaker read access
resource "aws_iam_role_policy" "lambda_sagemaker_access" {
  name = "${local.project_cfg["prefix"]}-${local.project_cfg["pipeline_name"]}-sagemaker"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:DescribeModelPackage",
          "sagemaker:DescribeProcessingJob",
          "sagemaker:ListTags"
        ]
        Resource = [
          "arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:model-package/*",
          "arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:processing-job/*"
        ]
      }
    ]
  })
}
