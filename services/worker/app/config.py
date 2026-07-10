"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        config.py
Module:      Worker / Configuration
Description:

Loads environment-based configuration required by the Face2Wap worker for
database access, internal API protection, face-swap processing, and local or
future cloud storage integration.

============================================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Face2Wap worker configuration."""

    database_url: str

    worker_api_token: str
    face_swap_device_id: int = 0

    storage_provider: str = "local"

    local_upload_dir: str = "/app/storage/uploads"
    local_result_dir: str = "/app/storage/results"
    local_temp_dir: str = "/app/storage/temp"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
