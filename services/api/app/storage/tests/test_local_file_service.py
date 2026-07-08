"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        test_local_file_service.py
Module:      API / Storage Tests
Description:

Tests local storage path resolution, file existence, deletion, result path
preparation, and path traversal protection.

============================================================================
"""

from pathlib import Path

import pytest

from app.config import settings
from app.storage.local_file_service import (
    delete_local_file,
    local_file_exists,
    prepare_local_result_path,
    resolve_local_result_file,
    resolve_local_upload_file,
)


def test_resolve_local_upload_file() -> None:
    """Resolve an upload object path under the configured upload directory."""

    object_path = "job_test/source_face_image/face.png"

    resolved_path = resolve_local_upload_file(object_path)

    expected_path = (
        Path(settings.local_upload_dir).resolve()
        / object_path
    ).resolve()

    assert resolved_path == expected_path


def test_resolve_local_result_file() -> None:
    """Resolve a result object path under the configured result directory."""

    object_path = "job_test/result.png"

    resolved_path = resolve_local_result_file(object_path)

    expected_path = (
        Path(settings.local_result_dir).resolve()
        / object_path
    ).resolve()

    assert resolved_path == expected_path


def test_local_file_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Return true when an uploaded local file exists."""

    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    object_path = "job_test/face.png"
    file_path = tmp_path / object_path

    file_path.parent.mkdir(parents=True)
    file_path.write_bytes(b"face2wap-test")

    assert local_file_exists(object_path) is True


def test_delete_local_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Delete an existing uploaded local file."""

    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    object_path = "job_test/face.png"
    file_path = tmp_path / object_path

    file_path.parent.mkdir(parents=True)
    file_path.write_bytes(b"face2wap-test")

    deleted = delete_local_file(object_path)

    assert deleted is True
    assert file_path.exists() is False


def test_delete_missing_local_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return false when deleting a missing local file."""

    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    deleted = delete_local_file("job_test/missing.png")

    assert deleted is False


def test_prepare_local_result_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prepare a result directory and return its object and local paths."""

    monkeypatch.setattr(settings, "local_result_dir", str(tmp_path))

    object_path, result_path = prepare_local_result_path(
        job_id="job_test",
        filename="result.png",
    )

    assert object_path == "job_test/result.png"
    assert result_path == (tmp_path / "job_test/result.png").resolve()
    assert result_path.parent.exists()


def test_upload_path_traversal_is_rejected() -> None:
    """Reject upload object paths that escape the storage root."""

    with pytest.raises(
        ValueError,
        match="Resolved path escaped configured storage root.",
    ):
        resolve_local_upload_file("../../outside.png")


def test_result_path_traversal_is_rejected() -> None:
    """Reject result object paths that escape the storage root."""

    with pytest.raises(
        ValueError,
        match="Resolved path escaped configured storage root.",
    ):
        resolve_local_result_file("../../outside.png")
        