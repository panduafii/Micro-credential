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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

