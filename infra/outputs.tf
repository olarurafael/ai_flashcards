output "app_url" {
  value = "https://${aws_cloudfront_distribution.app.domain_name}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ssm_prefix" {
  value = local.ssm_prefix
}

# Values for the GitHub repository variables the deploy workflow reads.
output "github_variables" {
  value = {
    AWS_REGION                 = var.region
    AWS_DEPLOY_ROLE_ARN        = aws_iam_role.deploy.arn
    ECR_REPOSITORY_URL         = aws_ecr_repository.api.repository_url
    LAMBDA_FUNCTION_NAME       = aws_lambda_function.api.function_name
    FRONTEND_BUCKET            = aws_s3_bucket.frontend.bucket
    CLOUDFRONT_DISTRIBUTION_ID = aws_cloudfront_distribution.app.id
  }
}
