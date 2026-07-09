"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        result_registry.py
Module:      Worker / Result Registry
Description:

Registers successfully generated worker result assets in PostgreSQL and marks
the associated Face2Wap job as completed.

Transaction ownership remains with the caller so the service can safely run
inside worker transactions and rollback-based integration tests.

============================================================================
"""

from pathlib import Path

import psycopg

from app.storage_result_writer import (
    copy_worker_result_file,
    prepare_worker_result_path,
)


def register_worker_result(
    connection: psycopg.Connection,
    *,
    job_id: str,
    source_path: Path,
    filename: str,
    mime_type: str,
) -> dict:
    """Store and register a generated worker result."""

    object_path, result_path = prepare_worker_result_path(
        job_id=job_id,
        filename=filename,
    )

    copy_worker_result_file(
        source_path=source_path,
        result_path=result_path,
    )

    try:
        result_size = result_path.stat().st_size

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
                    size_bytes,
                    uploaded_size_bytes,
                    upload_status,
                    validation_status,
                    uploaded_at,
                    completed_at
                )
                VALUES (
                    %s,
                    'RESULT',
                    'local',
                    %s,
                    %s,
                    'local',
                    %s,
                    %s,
                    'COMPLETED',
                    'VALIDATED',
                    NOW(),
                    NOW()
                )
                RETURNING id
                """,
                (
                    job_id,
                    object_path,
                    mime_type,
                    result_size,
                    result_size,
                ),
            )

            result_asset = cursor.fetchone()

            cursor.execute(
                """
                UPDATE jobs
                SET status = 'COMPLETED',
                    progress_percent = 100,
                    error_message = NULL,
                    updated_at = NOW()
                WHERE job_id = %s
                """,
                (job_id,),
            )

            if cursor.rowcount != 1:
                raise ValueError("Worker result job was not found.")

    except Exception:
        result_path.unlink(missing_ok=True)
        raise

    return {
        "assetId": result_asset["id"],
        "jobId": job_id,
        "assetType": "RESULT",
        "storageProvider": "local",
        "objectPath": object_path,
        "sizeBytes": result_size,
    }
