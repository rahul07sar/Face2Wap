"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        worker_result_ingest_service.py
Module:      API / Worker Result Ingest
Description:

Receives generated worker result files, stores them through the API storage
layer, and marks the parent job as completed.

============================================================================
"""

from datetime import datetime, timezone

import psycopg
from fastapi import HTTPException, UploadFile, status

from app.storage.factory import get_storage_provider
from app.storage.local import sanitize_filename


CHUNK_SIZE_BYTES = 64 * 1024


def _get_existing_result_asset(
    connection: psycopg.Connection,
    *,
    job_id: str,
) -> dict | None:
    """Return the latest completed result asset for an already completed job."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                object_path,
                storage_provider,
                size_bytes
            FROM job_assets
            WHERE job_id = %s
              AND asset_type = 'RESULT'
              AND upload_status = 'COMPLETED'
              AND validation_status = 'VALIDATED'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (job_id,),
        )
        return cursor.fetchone()


async def ingest_worker_result_upload(
    connection: psycopg.Connection,
    *,
    job_id: str,
    file: UploadFile,
) -> dict:
    """Store one generated worker result file and complete the job."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                job_id,
                status,
                expires_at
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,),
        )
        job = cursor.fetchone()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    if job["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Job has expired.",
        )

    if job["status"] == "COMPLETED":
        existing_result = _get_existing_result_asset(
            connection,
            job_id=job_id,
        )

        if not existing_result:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job result has already been stored.",
            )

        return {
            "assetId": existing_result["id"],
            "jobId": job_id,
            "assetType": "RESULT",
            "storageProvider": existing_result["storage_provider"],
            "objectPath": existing_result["object_path"],
            "sizeBytes": existing_result["size_bytes"],
            "status": "COMPLETED",
            "progressPercent": 100,
        }

    if job["status"] not in {"QUEUED", "PROCESSING"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is not ready to accept a worker result.",
        )

    storage = get_storage_provider()
    safe_filename = sanitize_filename(
        file.filename or "face2wap-result.bin",
    )
    prepared_result = storage.prepare_result(
        job_id=job_id,
        filename=safe_filename,
    )

    if (
        prepared_result.storage_provider != "local"
        or prepared_result.result_path is None
    ):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Worker result upload is unavailable for this storage provider.",
        )

    result_path = prepared_result.result_path
    result_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_size = 0

    try:
        with result_path.open("wb") as output:
            while True:
                chunk = await file.read(
                    CHUNK_SIZE_BYTES,
                )

                if not chunk:
                    break

                result_size += len(chunk)
                output.write(chunk)

        if result_size <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Worker result file is empty.",
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
                    prepared_result.object_path,
                    file.content_type or "application/octet-stream",
                    result_size,
                    result_size,
                ),
            )
            asset = cursor.fetchone()

            cursor.execute(
                """
                UPDATE jobs
                SET status = 'COMPLETED',
                    progress_percent = 100,
                    error_message = NULL,
                    updated_at = NOW()
                WHERE job_id = %s
                  AND status IN (
                      'QUEUED',
                      'PROCESSING'
                  )
                """,
                (job_id,),
            )

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Job result could not be registered.",
                )

    except Exception:
        result_path.unlink(
            missing_ok=True,
        )
        raise

    return {
        "assetId": asset["id"],
        "jobId": job_id,
        "assetType": "RESULT",
        "storageProvider": "local",
        "objectPath": prepared_result.object_path,
        "sizeBytes": result_size,
        "status": "COMPLETED",
        "progressPercent": 100,
    }
