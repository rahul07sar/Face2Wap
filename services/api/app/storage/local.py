"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        local.py
Module:      API / Storage
Description:

Provides local filesystem-backed storage preparation.

============================================================================
"""

import os
import re
from pathlib import Path

from app.config import settings
from app.storage.base import PreparedUpload, StorageProvider


SAFE_FILENAME_PATTERN = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """Return a safe filename for local storage paths."""

    cleaned = SAFE_FILENAME_PATTERN.sub("-", filename.strip())
    return cleaned[:120] or "upload.bin"


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider."""

    def prepare_upload(
        self,
        *,
        job_id: str,
        asset_type: str,
        filename: str,
        expires_in_seconds: int,
    ) -> PreparedUpload:
        """Create a local upload path and return an API upload URL."""

        safe_filename = sanitize_filename(filename)
        object_path = f"{job_id}/{asset_type.lower()}/{safe_filename}"

        upload_root = Path(settings.local_upload_dir)
        upload_dir = upload_root / job_id / asset_type.lower()
        upload_dir.mkdir(parents=True, exist_ok=True)

        return PreparedUpload(
            upload_url=f"/jobs/{job_id}/uploads/local/{asset_type}",
            object_path=object_path,
            storage_provider="local",
            expires_in_seconds=expires_in_seconds,
        )
    