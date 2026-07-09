"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        config.py
Module:      Worker / Configuration
Description:

Loads environment-based configuration required by the Face2Wap worker for
database access and local or future cloud storage integration.

============================================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Face2Wap worker configuration."""

    database_url: str

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
