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

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_env: str = "development"
    database_url: str
    job_token_secret: str
    job_expiry_hours: int = 24
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 20
    storage_provider: str = "local"
    local_upload_dir: str = "storage/uploads"
    local_result_dir: str = "storage/results"
    upload_url_expiry_minutes: int = 15
    max_image_size_mb: int = 10
    max_video_size_mb: int = 200
    max_video_duration_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()