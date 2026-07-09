"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        test_storage_result_writer.py
Module:      Worker / Storage Tests
Description:

Tests worker result path preparation, file copying, source preservation, and
path traversal protection without modifying real Face2Wap result files.

============================================================================
"""

from pathlib import Path

import pytest

from app.config import settings
from app.storage_result_writer import (
    copy_worker_result_file,
    prepare_worker_result_path,
)


def test_prepare_worker_result_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prepare a worker result path under the configured result directory."""

    monkeypatch.setattr(settings, "local_result_dir", str(tmp_path))

    object_path, result_path = prepare_worker_result_path(
        job_id="job_test",
        filename="result.png",
    )

    assert object_path == "job_test/result.png"
    assert result_path == (tmp_path / "job_test/result.png").resolve()
    assert result_path.parent.exists()


def test_copy_worker_result_file(tmp_path: Path) -> None:
    """Copy a generated worker file into result storage."""

    source_path = tmp_path / "generated.png"
    result_path = tmp_path / "results" / "job_test" / "result.png"

    content = b"face2wap-worker-result"
    source_path.write_bytes(content)

    copy_worker_result_file(
        source_path=source_path,
        result_path=result_path,
    )

    assert result_path.exists()
    assert result_path.read_bytes() == content


def test_copy_worker_result_preserves_source(tmp_path: Path) -> None:
    """Preserve the generated source file after result storage copying."""

    source_path = tmp_path / "generated.png"
    result_path = tmp_path / "results" / "result.png"

    source_path.write_bytes(b"face2wap-result")

    copy_worker_result_file(
        source_path=source_path,
        result_path=result_path,
    )

    assert source_path.exists()
    assert result_path.exists()


def test_worker_result_path_traversal_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject result paths that escape the configured storage root."""

    monkeypatch.setattr(settings, "local_result_dir", str(tmp_path))

    with pytest.raises(
        ValueError,
        match="Resolved path escaped configured storage root.",
    ):
        prepare_worker_result_path(
            job_id="../../outside",
            filename="result.png",
        )
