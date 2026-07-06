"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        factory.py
Module:      API / Storage
Description:

Selects the configured storage provider for upload and result asset handling.

============================================================================
"""

from fastapi import HTTPException, status

from app.config import settings
from app.storage.base import StorageProvider
from app.storage.gcs import GCSStorageProvider
from app.storage.local import LocalStorageProvider


def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider."""

    if settings.storage_provider == "local":
        return LocalStorageProvider()

    if settings.storage_provider == "gcs":
        return GCSStorageProvider()

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Invalid storage provider configuration.",
    )
