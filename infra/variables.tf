variable "project" {
  description = "Name prefix for every resource."
  type        = string
  default     = "ai-flashcards"
}

variable "region" {
  description = "AWS region. Keep the Neon database in the same region to keep latency low."
  type        = string
  default     = "eu-central-1"
}

variable "github_repo" {
  description = "owner/name of the repository allowed to deploy through GitHub Actions."
  type        = string
  default     = "olarurafael/ai_flashcards"
}

variable "create_github_oidc_provider" {
  description = "Set to false if the account already has the GitHub Actions OIDC provider."
  type        = bool
  default     = true
}

variable "bootstrap_image_tag" {
  description = "Image tag the Lambda is created with. Later deploys from CI replace it."
  type        = string
  default     = "bootstrap"
}

variable "api_rate_limit" {
  description = "Steady-state requests per second API Gateway allows, a backstop against abuse."
  type        = number
  default     = 10
}

variable "api_burst_limit" {
  description = "Burst requests API Gateway allows."
  type        = number
  default     = 20
}
