"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        upload_completion_service.py
Module:      API / Upload Completion Service
Description:

Finalizes validated upload assets and reports whether the parent job has all
required assets for future queue processing.

============================================================================
"""

from datetime import datetime, timezone

import psycopg
from fastapi import HTTPException, status


REQUIRED_ASSETS_BY_JOB_TYPE = {
    "IMAGE_SWAP": {"SOURCE_FACE_IMAGE", "TARGET_IMAGE"},
    "VIDEO_SWAP": {"SOURCE_FACE_IMAGE", "TARGET_VIDEO"},
}


def complete_validated_upload(
    connection: psycopg.Connection,
    *,
    job_id: str,
    asset_id: int,
) -> dict:
    """Mark a validated upload asset as completed."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ja.id,
                ja.job_id,
                ja.asset_type,
                ja.upload_status,
                ja.validation_status,
                ja.sha256_hash,
                ja.uploaded_size_bytes,
                ja.object_path,
                j.job_type,
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

    if asset["upload_status"] == "COMPLETED":
        return {
            "assetId": asset_id,
            "jobId": job_id,
            "assetType": asset["asset_type"],
            "uploadStatus": "COMPLETED",
            "jobReadyForQueue": _is_job_ready_for_queue(connection, job_id, asset["job_type"]),
        }

    if asset["upload_status"] != "VALIDATED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only validated uploads can be completed.",
        )

    if asset["validation_status"] != "VALIDATED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload validation is not complete.",
        )

    if not asset["sha256_hash"] or not asset["uploaded_size_bytes"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload metadata is incomplete.",
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE job_assets
            SET upload_status = 'COMPLETED',
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            """,
            (asset_id,),
        )

    return {
        "assetId": asset_id,
        "jobId": job_id,
        "assetType": asset["asset_type"],
        "uploadStatus": "COMPLETED",
        "jobReadyForQueue": _is_job_ready_for_queue(
            connection,
            job_id,
            asset["job_type"],
        ),
    }


def _is_job_ready_for_queue(
    connection: psycopg.Connection,
    job_id: str,
    job_type: str,
) -> bool:
    """Return whether all required assets for the job are completed."""

    required_assets = REQUIRED_ASSETS_BY_JOB_TYPE.get(job_type)

    if not required_assets:
        return False

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT asset_type
            FROM job_assets
            WHERE job_id = %s
              AND upload_status = 'COMPLETED'
            """,
            (job_id,),
        )
        completed_assets = {row["asset_type"] for row in cursor.fetchall()}

    return required_assets.issubset(completed_assets)
