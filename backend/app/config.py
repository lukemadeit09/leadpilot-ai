from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://leadpilot:leadpilot@localhost:5432/leadpilot"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(default="dev-only-change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_simple_model: str = "gpt-4.1-mini"
    openai_complex_model: str = "gpt-4.1"
    openai_embedding_model: str = "text-embedding-3-small"
    cors_origins: str = "http://localhost:3000"
    upload_dir: Path = Path("uploads")
    log_level: str = "INFO"
    trusted_hosts: str = "localhost,127.0.0.1"
    gunicorn_workers: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env.lower() != "production":
            return self
        if self.jwt_secret_key == "dev-only-change-me" or len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be a strong secret in production")
        if not self.database_url.startswith(("postgresql", "postgres://")):
            raise ValueError("DATABASE_URL must use PostgreSQL in production")
        if "*" in self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must not contain '*' in production")
        if not self.cors_origin_list:
            raise ValueError("CORS_ORIGINS must include the deployed frontend origin in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
