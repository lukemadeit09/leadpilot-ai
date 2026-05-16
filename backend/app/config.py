from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://leadpilot:leadpilot@localhost:5432/leadpilot"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_task_always_eager: bool = False
    jwt_secret_key: str = Field(default="dev-only-change-me")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "leadpilot-ai"
    access_token_expire_minutes: int = 1440
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_simple_model: str = "gpt-4.1-mini"
    openai_complex_model: str = "gpt-4.1"
    openai_embedding_model: str = "text-embedding-3-small"
    cors_origins: str = "http://localhost:3000"
    upload_dir: Path = Path("uploads")
    max_upload_bytes: int = 10 * 1024 * 1024
    rate_limit_auth_per_minute: int = 20
    rate_limit_ai_per_minute: int = 60
    rate_limit_billing_per_minute: int = 60
    rate_limit_public_per_minute: int = 120
    failed_login_lock_threshold: int = 5
    failed_login_lock_minutes: int = 15
    log_level: str = "INFO"
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.app_env == "production" and "*" in origins:
            raise ValueError("CORS_ORIGINS cannot include '*' in production")
        return origins

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend_url(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
