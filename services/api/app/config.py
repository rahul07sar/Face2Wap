"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        config.py
Module:      API / Configuration
Description:

Loads and validates runtime configuration for the Face2Wap API service.

============================================================================
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_env: str = "development"
    database_url: str
    job_token_secret: str
    job_expiry_hours: int = 24
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()