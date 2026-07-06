"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        local_writer.py
Module:      API / Storage
Description:

Streams uploaded files to local storage using constant memory.

============================================================================
"""

from pathlib import Path

from app.config import settings


def resolve_local_upload_path(object_path: str) -> Path:
    """Resolve a safe local upload path under the configured upload directory."""

    upload_root = Path(settings.local_upload_dir).resolve()
    target_path = (upload_root / object_path).resolve()

    if upload_root not in target_path.parents:
        raise ValueError("Resolved upload path escaped upload directory.")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path