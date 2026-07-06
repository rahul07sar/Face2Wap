"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        gcs.py
Module:      API / Storage
Description:

Provides Google Cloud Storage provider placeholder. The interface
is kept ready so local storage can later be swapped with GCS without changing
API contracts.

============================================================================
"""

from fastapi import HTTPException, status

from app.storage.base import PreparedUpload, StorageProvider


class GCSStorageProvider(StorageProvider):
    """Google Cloud Storage provider placeholder."""

    def prepare_upload(
        self,
        *,
        job_id: str,
        asset_type: str,
        filename: str,
        expires_in_seconds: int,
    ) -> PreparedUpload:
        """Prepare a future GCS signed upload URL."""

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GCS storage provider is not enabled yet.",
        )