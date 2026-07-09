"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        storage_result_writer.py
Module:      Worker / Storage
Description:

Writes generated worker result files into local result storage. This module
will later be extended to support Google Cloud Storage through the same worker
flow.

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


def prepare_worker_result_path(
    *,
    job_id: str,
    filename: str,
) -> tuple[str, Path]:
    """Prepare a local result object path and filesystem path."""

    object_path = f"{job_id}/{filename}"
    result_path = _resolve_under_root(
        settings.local_result_dir,
        object_path,
    )

    result_path.parent.mkdir(parents=True, exist_ok=True)

    return object_path, result_path


def copy_worker_result_file(
    *,
    source_path: Path,
    result_path: Path,
) -> None:
    """Copy a generated worker result file into result storage."""

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_bytes(source_path.read_bytes())
    