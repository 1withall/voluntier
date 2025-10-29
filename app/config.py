"""Application configuration using pydantic-settings.

This module provides centralized configuration management for the Voluntier
application, loading settings from environment variables with validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden by environment variables or a .env file.
    Database URLs, API keys, and secrets should never be hardcoded.

    Attributes:
        app_name: Application name for logging and identification.
        debug: Enable debug mode (never use in production).
        environment: Deployment environment (development/staging/production).
        database_url: PostgreSQL connection string with asyncpg driver.
        database_test_url: Test database connection string.
        secret_key: Secret key for JWT token signing (generate with secrets.token_hex(32)).
        algorithm: JWT signing algorithm (HS256 recommended).
        access_token_expire_minutes: JWT access token expiration time.
        refresh_token_expire_days: JWT refresh token expiration time.
        redis_url: Redis connection string for caching and sessions.
        cors_origins: List of allowed CORS origins.
        rate_limit_per_minute: Rate limit for authentication endpoints.

    Example:
        >>> from app.config import settings
        >>> settings.app_name
        'Voluntier'
        >>> settings.debug
        False
    """

    # Application
    app_name: str = "Voluntier"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/voluntier"
    database_test_url: str = (
        "postgresql+asyncpg://user:password@localhost:5432/voluntier_test"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Security
    secret_key: str = (
        "CHANGE-ME-IN-PRODUCTION"  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8081"]

    # Rate Limiting
    rate_limit_per_minute: int = 10

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Global settings instance
settings = Settings()
