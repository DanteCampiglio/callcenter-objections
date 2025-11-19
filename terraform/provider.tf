terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.33.0"
    }
  }
  backend "s3" {
    bucket               = "dss-tf-states"
    key                  = "se_churn_ar/terraform.tfstate"
    region               = "eu-central-1"
    dynamodb_table       = "dss-tf-states-lock"
    encrypt              = true
    workspace_key_prefix = "workspaces/se_churn_ar"
  }
}

provider "aws" {
  region = "eu-central-1"

  default_tags {
    tags = {
      Application   = upper("${local.project_cfg["prefix"]}")
      "Cost Center" = "${local.project_cfg["cost_center"]}"
    }
  }
}
