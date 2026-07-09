"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        temp_cleanup_service.py
Module:      API / Cleanup
Description:

Deletes stale local temporary files that exceed the configured maximum age.

============================================================================
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings


def cleanup_stale_temp_files() -> dict:
    """Delete temporary files older than the configured maximum age."""

    temp_root = Path(settings.local_temp_dir).resolve()

    if not temp_root.exists():
        return {
            "deletedTempFiles": 0,
        }

    cutoff_time = datetime.now(timezone.utc) - timedelta(
        minutes=settings.cleanup_temp_file_max_age_minutes,
    )

    deleted_files = 0

    for file_path in temp_root.rglob("*"):
        if not file_path.is_file():
            continue

        modified_at = datetime.fromtimestamp(
            file_path.stat().st_mtime,
            tz=timezone.utc,
)

        if modified_at >= cutoff_time:
            continue

        file_path.unlink()
        deleted_files += 1

    _remove_empty_directories(temp_root)

    return {
        "deletedTempFiles": deleted_files,
    }


def _remove_empty_directories(root_path: Path) -> None:
    """Remove empty directories below the configured temporary storage root."""

    directories = sorted(
        (
            path
            for path in root_path.rglob("*")
            if path.is_dir()
        ),
        key=lambda path: len(path.parts),
        reverse=True,
    )

    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            continue
