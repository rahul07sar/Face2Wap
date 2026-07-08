"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        local_file_service.py
Module:      API / Storage
Description:

Provides local storage read, delete, and result-path helpers for uploaded and
generated Face2Wap assets.

============================================================================
"""

from pathlib import Path

from app.config import settings


def _resolve_under_root(root: str, object_path: str) -> Path:
    """Resolve an object path safely under a configured storage root."""

    storage_root = Path(root).resolve()
    target_path = (storage_root / object_path).resolve()

    if storage_root not in target_path.parents and target_path != storage_root:
        raise ValueError("Resolved path escaped configured storage root.")

    return target_path


def resolve_local_upload_file(object_path: str) -> Path:
    """Resolve an uploaded asset path."""

    return _resolve_under_root(settings.local_upload_dir, object_path)


def resolve_local_result_file(object_path: str) -> Path:
    """Resolve a result asset path."""

    return _resolve_under_root(settings.local_result_dir, object_path)


def local_file_exists(object_path: str, *, is_result: bool = False) -> bool:
    """Return whether a local storage object exists."""

    path = (
        resolve_local_result_file(object_path)
        if is_result
        else resolve_local_upload_file(object_path)
    )

    return path.exists() and path.is_file()


def delete_local_file(object_path: str, *, is_result: bool = False) -> bool:
    """Delete a local storage object if it exists."""

    path = (
        resolve_local_result_file(object_path)
        if is_result
        else resolve_local_upload_file(object_path)
    )

    if not path.exists():
        return False

    path.unlink()
    return True


def prepare_local_result_path(job_id: str, filename: str) -> tuple[str, Path]:
    """Create and return a result object path and filesystem path."""

    object_path = f"{job_id}/{filename}"
    result_path = resolve_local_result_file(object_path)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    return object_path, result_path
