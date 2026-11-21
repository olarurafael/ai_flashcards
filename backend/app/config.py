import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_ssm_parameters(prefix: str) -> None:
    """Copy SSM parameters under `prefix` into the environment.

    Secrets live in SSM Parameter Store instead of Terraform state or the
    Lambda configuration. This runs once per cold start.
    """
    import boto3

    paginator = boto3.client("ssm").get_paginator("get_parameters_by_path")
    for page in paginator.paginate(Path=prefix, WithDecryption=True):
        for param in page["Parameters"]:
            name = param["Name"].rsplit("/", 1)[-1].upper()
            os.environ.setdefault(name, param["Value"])


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_ttl_hours: int = 24 * 7

    openai_api_key: str = ""
    # Benchmarked against gpt-4o-mini and gpt-5-nano on the same text: cheapest
    # per generation, fastest, and it doesn't pad decks with invented cards.
    openai_model: str = "gpt-6-luna"

    # Only needed when the frontend is served from a different origin;
    # in production CloudFront serves both under one domain.
    cors_origins: list[str] = []

    max_input_chars: int = 20_000
    # Lambda caps requests at 6 MB and API Gateway base64-encodes uploads (+33%).
    max_pdf_bytes: int = 3 * 1024 * 1024
    max_cards_per_generation: int = 20

    # Generation calls cost money, so they are capped per user and globally.
    daily_generations_per_user: int = 20
    daily_generations_per_guest: int = 5
    daily_generations_global: int = 100

    @property
    def sqlalchemy_url(self) -> str:
        return to_sqlalchemy_url(self.database_url)


def to_sqlalchemy_url(url: str) -> str:
    """Point plain postgres:// URLs (as Neon and most hosts give them) at psycopg 3."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


@lru_cache
def get_settings() -> Settings:
    prefix = os.getenv("SSM_PARAMETER_PREFIX")
    if prefix:
        _load_ssm_parameters(prefix)
    return Settings()
