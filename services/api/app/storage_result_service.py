"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        storage_result_service.py
Module:      API / Storage Result Service
Description:

Provides result asset registration helpers for future worker-generated
Face2Wap image and video outputs.

It will be used in Phase 4 when the worker generates image and video results.

============================================================================
"""

from pathlib import Path

import psycopg

from app.storage.factory import get_storage_provider


def prepare_result_asset(
    connection: psycopg.Connection,
    *,
    job_id: str,
    filename: str,
    mime_type: str,
) -> dict:
    """Prepare a result asset path and register it in the database."""

    storage = get_storage_provider()
    prepared_result = storage.prepare_result(
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
            VALUES (%s, 'RESULT', %s, %s, %s, %s, 'COMPLETED', 'VALIDATED', NOW())
            RETURNING id
            """,
            (
                job_id,
                prepared_result.storage_provider,
                prepared_result.object_path,
                mime_type,
                prepared_result.storage_provider,
            ),
        )
        asset = cursor.fetchone()

    return {
        "assetId": asset["id"],
        "jobId": job_id,
        "assetType": "RESULT",
        "storageProvider": prepared_result.storage_provider,
        "objectPath": prepared_result.object_path,
        "resultPath": (
            str(prepared_result.result_path)
            if prepared_result.result_path
            else None
        ),
    }


def copy_local_result_file(
    *,
    source_path: Path,
    result_path: Path,
) -> None:
    """Copy a generated file into the local result storage path."""

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_bytes(source_path.read_bytes())
    