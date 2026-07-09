"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        gcs.py
Module:      API / Storage
Description:

Provides the Google Cloud Storage provider placeholder and preserves the
storage provider contract for future GCS integration.

============================================================================
"""

from fastapi import HTTPException, status

from app.storage.base import PreparedResult, PreparedUpload, StorageProvider


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

        self._raise_not_implemented()

    def file_exists(
        self,
        *,
        object_path: str,
        is_result: bool = False,
    ) -> bool:
        """Check whether a future GCS object exists."""

        self._raise_not_implemented()

    def delete_file(
        self,
        *,
        object_path: str,
        is_result: bool = False,
    ) -> bool:
        """Delete a future GCS object."""

        self._raise_not_implemented()

    def prepare_result(
        self,
        *,
        job_id: str,
        filename: str,
    ) -> PreparedResult:
        """Prepare a future GCS result destination."""

        self._raise_not_implemented()

    @staticmethod
    def _raise_not_implemented() -> None:
        """Raise the standard response for unavailable GCS operations."""

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GCS storage provider is not enabled yet.",
        )
    