"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        base.py
Module:      API / Storage
Description:

Defines the storage provider contract used by local and future cloud storage
implementations.

============================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PreparedUpload:
    """Prepared upload response returned by storage providers."""

    upload_url: str
    object_path: str
    storage_provider: str
    expires_in_seconds: int


class StorageProvider(ABC):
    """Base storage provider interface."""

    @abstractmethod
    def prepare_upload(
        self,
        *,
        job_id: str,
        asset_type: str,
        filename: str,
        expires_in_seconds: int,
    ) -> PreparedUpload:
        """Prepare an upload destination."""