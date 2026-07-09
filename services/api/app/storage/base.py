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
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class PreparedUpload:
    """Prepared upload response returned by storage providers."""

    upload_url: str
    object_path: str
    storage_provider: str
    expires_in_seconds: int


@dataclass(frozen=True)
class PreparedResult:
    """Prepared result path returned by storage providers."""

    object_path: str
    storage_provider: str
    result_path: Optional[Path] = None


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

    @abstractmethod
    def file_exists(self, *, object_path: str, is_result: bool = False) -> bool:
        """Return whether a storage object exists."""

    @abstractmethod
    def delete_file(self, *, object_path: str, is_result: bool = False) -> bool:
        """Delete a storage object if it exists."""

    @abstractmethod
    def prepare_result(self, *, job_id: str, filename: str) -> PreparedResult:
        """Prepare a result destination."""
        