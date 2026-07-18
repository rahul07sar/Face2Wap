"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        upload_retry_service.py
Module:      API / Upload Retry Service
Description:

Resets failed upload assets so the same prepared asset can be uploaded again
with the same filename, MIME type, and expected size.

============================================================================
"""

from datetime import datetime, timedelta, timezone

import psycopg
from fastapi import HTTPException, status

from app.storage.local_writer import resolve_local_upload_path
from app.upload_service import get_upload_expiry_minutes
from app.video_upload_service import (
    reset_video_upload_metadata,
)


def retry_failed_upload(
    connection: psycopg.Connection,
    *,
    job_id: str,
    asset_id: int,
) -> dict:
    """Reset a failed upload asset back to PREPARED."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ja.id,
                ja.job_id,
                ja.asset_type,
                ja.object_path,
                ja.upload_status,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload asset not found.",
        )

    if asset["job_expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Job has expired.",
        )

    if asset["upload_status"] != "FAILED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed upload assets can be retried.",
        )

    # Defensive cleanup in case a failed upload left a partial file behind.
    target_path = resolve_local_upload_path(asset["object_path"])
    target_path.unlink(missing_ok=True)

    upload_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=get_upload_expiry_minutes(asset["asset_type"])
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE job_assets
            SET upload_status = 'PREPARED',
                validation_status = NULL,
                validation_error = NULL,
                sha256_hash = NULL,
                uploaded_size_bytes = NULL,
                uploaded_at = NULL,
                width = NULL,
                height = NULL,
                duration_seconds = NULL,
                upload_expires_at = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (upload_expires_at, asset_id),
        )

    if asset["asset_type"] == "TARGET_VIDEO":
        reset_video_upload_metadata(
            connection,
            asset_id=asset_id,
        )

    return {
        "assetId": asset_id,
        "jobId": job_id,
        "assetType": asset["asset_type"],
        "uploadStatus": "PREPARED",
        "uploadUrl": f"/jobs/{job_id}/assets/{asset_id}/upload",
        "uploadExpiresAt": upload_expires_at,
    }
