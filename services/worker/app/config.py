"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        config.py
Module:      Worker / Configuration
Description:

Loads environment-based configuration required by the Face2Wap worker for
database access, internal API protection, pluggable face-swap processing, and
local or future cloud storage integration.

============================================================================
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


FaceSwapEngineName = Literal[
    "socaity",
    "facefusion",
]


class Settings(BaseSettings):
    """Face2Wap worker configuration."""

    database_url: str

    worker_api_token: str
    face_swap_device_id: int = 0
    face_swap_engine: FaceSwapEngineName = "facefusion"
    facefusion_python_executable: str = "python3"
    facefusion_working_directory: str = "/opt/facefusion"
    facefusion_execution_provider: str = "cpu"
    facefusion_execution_thread_count: int = 4
    facefusion_download_providers: str = "github"
    facefusion_download_scope: str = "lite"
    facefusion_face_swapper_model: str = "hyperswap_1c_256"
    facefusion_face_swapper_pixel_boost: str = "512x512"
    facefusion_enable_face_enhancer: bool = True
    facefusion_face_enhancer_model: str = "gfpgan_1.4"
    facefusion_face_enhancer_blend: int = 80
    facefusion_face_enhancer_weight: float = 1.0
    facefusion_log_level: str = "error"
    facefusion_keep_temp: bool = False
    facefusion_output_image_quality: int = 95
    facefusion_process_timeout_seconds: int = 900

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
