"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        upload_service.py
Module:      API / Upload Service
Description:

Creates upload records and prepares local or cloud upload destinations.

============================================================================
"""

from datetime import UTC, datetime, timedelta

import psycopg
from fastapi import HTTPException, status

from app.config import settings
from app.storage.factory import get_storage_provider
from app.upload_validation import validate_upload_request


def prepare_job_upload(
    connection: psycopg.Connection,
    *,
    job_id: str,
    asset_type: str,
    filename: str,
    mime_type: str,
    size_bytes: int,
) -> dict:
    """Prepare an upload slot for a job asset."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT job_id, job_type, status, expires_at
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,),
        )
        job = cursor.fetchone()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["expires_at"] <= datetime.now(UTC):
        raise HTTPException(status_code=410, detail="Job has expired.")

    validate_upload_request(
        job_type=job["job_type"],
        asset_type=asset_type,
        mime_type=mime_type,
        size_bytes=size_bytes,
    )

    expires_in_seconds = settings.upload_url_expiry_minutes * 60
    upload_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in_seconds)

    storage = get_storage_provider()
    prepared = storage.prepare_upload(
        job_id=job_id,
        asset_type=asset_type,
        filename=filename,
        expires_in_seconds=expires_in_seconds,
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
                size_bytes,
                storage_provider,
                upload_status,
                upload_expires_at,
                original_filename
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'PREPARED', %s, %s)
            RETURNING id
            """,
            (
                job_id,
                asset_type,
                "local",
                prepared.object_path,
                mime_type,
                size_bytes,
                prepared.storage_provider,
                upload_expires_at,
                filename,
            ),
        )
        asset = cursor.fetchone()

    return {
        "assetId": asset["id"],
        "uploadUrl": f"/jobs/{job_id}/assets/{asset['id']}/upload",
        "objectPath": prepared.object_path,
        "storageProvider": prepared.storage_provider,
        "uploadExpiresAt": upload_expires_at,
    }
