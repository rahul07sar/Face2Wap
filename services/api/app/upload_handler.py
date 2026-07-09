"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        upload_handler.py
Module:      API / Upload Handler
Description:

Handles multipart uploads with streaming writes, SHA-256 hashing, expiry
checks, ownership checks, metadata validation, cleanup, and asset state
updates.

============================================================================
"""

from datetime import datetime, timezone

import psycopg
from fastapi import HTTPException, UploadFile, status

from app.file_hash import create_sha256_hasher
from app.file_metadata import extract_file_metadata
from app.storage.local_writer import resolve_local_upload_path


CHUNK_SIZE_BYTES = 64 * 1024


def _mark_asset_failed(
    connection: psycopg.Connection,
    *,
    asset_id: int,
    validation_error: str,
) -> None:
    """Persist a failed upload/validation state for a job asset."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE job_assets
            SET upload_status = 'FAILED',
                validation_status = 'FAILED',
                validation_error = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (validation_error, asset_id),
        )

    connection.commit()


async def upload_job_asset(
    connection: psycopg.Connection,
    *,
    job_id: str,
    asset_id: int,
    file: UploadFile,
) -> dict:
    """Upload a prepared job asset to local storage."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ja.id,
                ja.job_id,
                ja.asset_type,
                ja.object_path,
                ja.mime_type,
                ja.size_bytes,
                ja.upload_status,
                ja.upload_expires_at,
                j.expires_at AS job_expires_at
            FROM job_assets ja
            JOIN jobs j ON j.job_id = ja.job_id
            WHERE ja.id = %s
              AND ja.job_id = %s
            """,
            (asset_id, job_id),
        )
        asset = cursor.fetchone()

    if not asset:
        raise HTTPException(status_code=404, detail="Upload asset not found.")

    now = datetime.now(timezone.utc)

    if asset["job_expires_at"] <= now:
        raise HTTPException(status_code=410, detail="Job has expired.")

    if asset["upload_expires_at"] and asset["upload_expires_at"] <= now:
        raise HTTPException(status_code=410, detail="Upload slot has expired.")

    if asset["upload_status"] not in {"PREPARED", "FAILED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Asset is not ready for upload.",
        )

    if file.content_type != asset["mime_type"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file MIME type does not match prepared asset.",
        )

    target_path = resolve_local_upload_path(asset["object_path"])

    hasher = create_sha256_hasher()
    total_size = 0

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE job_assets
            SET upload_status = 'UPLOADING',
                updated_at = NOW()
            WHERE id = %s
            """,
            (asset_id,),
        )
    connection.commit()

    try:
        with target_path.open("wb") as output:
            while True:
                chunk = await file.read(CHUNK_SIZE_BYTES)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > asset["size_bytes"]:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Uploaded file exceeds prepared size.",
                    )

                hasher.update(chunk)
                output.write(chunk)

    except HTTPException as error:
        target_path.unlink(missing_ok=True)
        _mark_asset_failed(
            connection,
            asset_id=asset_id,
            validation_error=str(error.detail),
        )
        raise

    except Exception as error:
        target_path.unlink(missing_ok=True)
        _mark_asset_failed(
            connection,
            asset_id=asset_id,
            validation_error="Upload failed while writing file.",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed while writing file.",
        ) from error

    if total_size != asset["size_bytes"]:
        target_path.unlink(missing_ok=True)
        _mark_asset_failed(
            connection,
            asset_id=asset_id,
            validation_error="Uploaded file size does not match prepared size.",
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file size does not match prepared size.",
        )

    try:
        metadata = extract_file_metadata(
            target_path,
            asset["mime_type"],
        )

    except ValueError as error:
        target_path.unlink(missing_ok=True)
        _mark_asset_failed(
            connection,
            asset_id=asset_id,
            validation_error=str(error),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE job_assets
            SET upload_status = 'VALIDATED',
                validation_status = 'VALIDATED',
                validation_error = NULL,
                sha256_hash = %s,
                uploaded_size_bytes = %s,
                uploaded_at = NOW(),
                width = %s,
                height = %s,
                duration_seconds = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                hasher.hexdigest(),
                total_size,
                metadata["width"],
                metadata["height"],
                metadata["duration_seconds"],
                asset_id,
            ),
        )

    return {
        "assetId": asset_id,
        "jobId": job_id,
        "assetType": asset["asset_type"],
        "uploadStatus": "VALIDATED",
        "sha256": hasher.hexdigest(),
        "sizeBytes": total_size,
        "objectPath": asset["object_path"],
        "width": metadata["width"],
        "height": metadata["height"],
        "durationSeconds": metadata["duration_seconds"],
    }
