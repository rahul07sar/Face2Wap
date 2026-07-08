"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        storage_result_service.py
Module:      API / Storage Result Service
Description:

Provides local result asset registration helpers for future worker-generated
Face2Wap image and video outputs.

It will be used in Phase 4 when the worker generates the image result.

============================================================================
"""

from pathlib import Path

import psycopg

from app.storage.local_file_service import prepare_local_result_path


def prepare_result_asset(
    connection: psycopg.Connection,
    *,
    job_id: str,
    filename: str,
    mime_type: str,
) -> dict:
    """Prepare a local result asset path and register it in the database."""

    object_path, result_path = prepare_local_result_path(
        job_id=job_id,
        filename=filename,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO job_assets (
                job_id,
                asset_type,
                bucket_name,
                object_path,
                mime_type,
                storage_provider,
                upload_status,
                validation_status,
                completed_at
            )
            VALUES (%s, 'RESULT', 'local', %s, %s, 'local', 'COMPLETED', 'VALIDATED', NOW())
            RETURNING id
            """,
            (
                job_id,
                object_path,
                mime_type,
            ),
        )
        asset = cursor.fetchone()

    return {
        "assetId": asset["id"],
        "jobId": job_id,
        "assetType": "RESULT",
        "storageProvider": "local",
        "objectPath": object_path,
        "resultPath": str(result_path),
    }


def copy_local_result_file(
    *,
    source_path: Path,
    result_path: Path,
) -> None:
    """Copy a generated file into the local result storage path."""

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_bytes(source_path.read_bytes())
