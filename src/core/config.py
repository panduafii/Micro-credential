from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment."""

    app_name: str = Field(default="MicroCred API", validation_alias="APP_NAME")
    environment: str = Field(default="local", validation_alias="APP_ENV")
    version: str = Field(default="0.1.0")
    jwt_secret: str = Field(default="replace-with-secure-secret", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256")
    access_token_ttl_seconds: int = Field(default=3600)
    allowed_roles: tuple[str, ...] = Field(
        default=("student", "advisor", "admin"), validation_alias="ALLOWED_ROLES"
    )
    database_url: str = Field(
        default="postgresql+asyncpg://microcred:postgres-password@localhost:5432/microcred",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )

    @property
    def async_database_url(self) -> str:
        """Convert database URL to async format (postgresql+asyncpg://)."""
        url = self.database_url
        # Render provides postgresql:// but we need postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # OpenAI/GPT Configuration
    openai_api_key: str = Field(
        default="",
        validation_alias="OPENAI_API_KEY",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="OPENAI_MODEL",
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="OPENAI_BASE_URL",
    )
    gpt_max_retries: int = Field(default=3, validation_alias="GPT_MAX_RETRIES")
    gpt_timeout_seconds: int = Field(default=60, validation_alias="GPT_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
