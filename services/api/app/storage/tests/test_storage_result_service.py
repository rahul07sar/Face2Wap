"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        test_storage_result_service.py
Module:      API / Storage Tests
Description:

Tests local result file copying and result storage behavior without modifying
real Face2Wap result files.

============================================================================
"""

from pathlib import Path

from app.storage_result_service import copy_local_result_file


def test_copy_local_result_file(tmp_path: Path) -> None:
    """Copy a generated file into the prepared local result path."""

    source_path = tmp_path / "generated.png"
    result_path = tmp_path / "results" / "job_test" / "result.png"

    source_content = b"face2wap-generated-result"
    source_path.write_bytes(source_content)

    copy_local_result_file(
        source_path=source_path,
        result_path=result_path,
    )

    assert result_path.exists()
    assert result_path.is_file()
    assert result_path.read_bytes() == source_content


def test_copy_local_result_file_creates_parent_directories(
    tmp_path: Path,
) -> None:
    """Create missing result directories before copying the file."""

    source_path = tmp_path / "generated.mp4"
    result_path = (
        tmp_path
        / "results"
        / "job_test"
        / "nested"
        / "result.mp4"
    )

    source_path.write_bytes(b"face2wap-video-result")

    assert result_path.parent.exists() is False

    copy_local_result_file(
        source_path=source_path,
        result_path=result_path,
    )

    assert result_path.parent.exists()
    assert result_path.exists()


def test_copy_local_result_file_preserves_source(
    tmp_path: Path,
) -> None:
    """Preserve the generated source file after copying the result."""

    source_path = tmp_path / "generated.png"
    result_path = tmp_path / "results" / "result.png"

    source_path.write_bytes(b"face2wap-result")

    copy_local_result_file(
        source_path=source_path,
        result_path=result_path,
    )

    assert source_path.exists()
    assert result_path.exists()
    