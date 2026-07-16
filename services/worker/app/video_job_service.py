"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        video_job_service.py
Module:      Worker / Video Job Service
Description:

Claims ready video face-swap jobs from PostgreSQL and resolves the validated
source image and target video assets required by the worker processing
pipeline.

The service uses row locking to prevent multiple workers from claiming the
same job concurrently. Transaction ownership remains with the caller.

============================================================================
"""

from typing import Optional

import psycopg


# ============================================================================
# Exceptions
# ============================================================================

class VideoJobError(RuntimeError):
    """Raised when a video face-swap job cannot be claimed or loaded."""


# ============================================================================
# Video Job Claiming
# ============================================================================

def claim_video_swap_job(
    connection: psycopg.Connection,
    *,
    job_id: str,
) -> dict:
    """Claim one ready video face-swap job and return its required assets."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                job_id,
                job_type,
                status,
                progress_percent,
                expires_at
            FROM jobs
            WHERE job_id = %s
            FOR UPDATE
            """,
            (job_id,),
        )

        job = cursor.fetchone()

        if not job:
            raise VideoJobError(
                "Video face-swap job was not found.",
            )

        if job["job_type"] != "VIDEO_SWAP":
            raise VideoJobError(
                "Job is not a video face-swap job.",
            )

        if job["status"] != "QUEUED":
            raise VideoJobError(
                "Video face-swap job is not ready for processing.",
            )

        cursor.execute(
            """
            SELECT
                id,
                asset_type,
                object_path,
                mime_type,
                storage_provider
            FROM job_assets
            WHERE job_id = %s
              AND asset_type IN (
                  'SOURCE_FACE_IMAGE',
                  'TARGET_VIDEO'
              )
              AND upload_status = 'COMPLETED'
              AND validation_status = 'VALIDATED'
            ORDER BY id ASC
            """,
            (job_id,),
        )

        assets = cursor.fetchall()

        source_asset: Optional[dict] = None
        target_asset: Optional[dict] = None

        for asset in assets:
            if (
                asset["asset_type"]
                == "SOURCE_FACE_IMAGE"
            ):
                source_asset = asset

            elif (
                asset["asset_type"]
                == "TARGET_VIDEO"
            ):
                target_asset = asset

        if source_asset is None:
            raise VideoJobError(
                "Validated source face image was not found.",
            )

        if target_asset is None:
            raise VideoJobError(
                "Validated target video was not found.",
            )

        if (
            source_asset["storage_provider"] != "local"
            or target_asset["storage_provider"] != "local"
        ):
            raise VideoJobError(
                "Video processing currently requires local storage assets.",
            )

        cursor.execute(
            """
            UPDATE jobs
            SET status = 'PROCESSING',
                progress_percent = 10,
                error_message = NULL,
                updated_at = NOW()
            WHERE job_id = %s
              AND status = 'QUEUED'
            """,
            (job_id,),
        )

        if cursor.rowcount != 1:
            raise VideoJobError(
                "Video face-swap job could not be claimed.",
            )

    return {
        "jobId": job["job_id"],
        "jobType": job["job_type"],
        "status": "PROCESSING",
        "progressPercent": 10,
        "sourceAssetId": source_asset["id"],
        "sourceObjectPath": source_asset["object_path"],
        "sourceMimeType": source_asset["mime_type"],
        "targetAssetId": target_asset["id"],
        "targetObjectPath": target_asset["object_path"],
        "targetMimeType": target_asset["mime_type"],
    }
