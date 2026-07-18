"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        config.py
Module:      API / Configuration
Description:

Loads and validates runtime configuration for the Face2Wap API service,
including database, storage, upload, cleanup, and internal worker settings.

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
    job_status_rate_limit_max_requests: int = 120

    storage_provider: str = "local"
    local_upload_dir: str = "storage/uploads"
    local_result_dir: str = "storage/results"
    local_temp_dir: str = "storage/temp"

    upload_url_expiry_minutes: int = 15
    video_upload_url_expiry_minutes: int = 180
    cleanup_batch_size: int = 100
    cleanup_temp_file_max_age_minutes: int = 60

    max_image_size_mb: int = 50
    max_video_size_mb: int = 2048
    max_video_duration_seconds: int = 60

    cors_allowed_origins: str = ""

    worker_base_url: str
    worker_api_token: str
    worker_request_timeout_seconds: int = 2100

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
