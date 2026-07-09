"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        test_temp_cleanup_service.py
Module:      API / Cleanup Tests
Description:

Tests stale temp-file deletion, fresh temp-file preservation, missing temp
directory handling, and empty-directory cleanup.

============================================================================
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings
from app.temp_cleanup_service import cleanup_stale_temp_files


def test_cleanup_stale_temp_files_deletes_old_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Delete temp files older than the configured maximum age."""

    monkeypatch.setattr(settings, "local_temp_dir", str(tmp_path))
    monkeypatch.setattr(settings, "cleanup_temp_file_max_age_minutes", 60)

    stale_file = tmp_path / "stale.tmp"
    stale_file.write_text("old temp", encoding="utf-8")

    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    os.utime(stale_file, (old_time.timestamp(), old_time.timestamp()))

    result = cleanup_stale_temp_files()

    assert result == {"deletedTempFiles": 1}
    assert stale_file.exists() is False


def test_cleanup_stale_temp_files_preserves_fresh_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Preserve temp files newer than the configured maximum age."""

    monkeypatch.setattr(settings, "local_temp_dir", str(tmp_path))
    monkeypatch.setattr(settings, "cleanup_temp_file_max_age_minutes", 60)

    fresh_file = tmp_path / "fresh.tmp"
    fresh_file.write_text("fresh temp", encoding="utf-8")

    result = cleanup_stale_temp_files()

    assert result == {"deletedTempFiles": 0}
    assert fresh_file.exists()


def test_cleanup_stale_temp_files_handles_missing_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Return zero when the temp directory does not exist."""

    missing_dir = tmp_path / "missing"

    monkeypatch.setattr(settings, "local_temp_dir", str(missing_dir))

    result = cleanup_stale_temp_files()

    assert result == {"deletedTempFiles": 0}


def test_cleanup_stale_temp_files_removes_empty_directories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Remove empty directories left after stale temp-file deletion."""

    monkeypatch.setattr(settings, "local_temp_dir", str(tmp_path))
    monkeypatch.setattr(settings, "cleanup_temp_file_max_age_minutes", 60)

    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()

    stale_file = nested_dir / "stale.tmp"
    stale_file.write_text("old temp", encoding="utf-8")

    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    os.utime(stale_file, (old_time.timestamp(), old_time.timestamp()))

    result = cleanup_stale_temp_files()

    assert result == {"deletedTempFiles": 1}
    assert stale_file.exists() is False
    assert nested_dir.exists() is False
    