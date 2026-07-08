"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        upload_progress_service.py
Module:      API / Upload Progress Service
Description:

Returns upload progress information for a job asset.

============================================================================
"""

import psycopg
from fastapi import HTTPException, status


def get_asset_upload_progress(
    connection: psycopg.Connection,
    *,
    job_id: str,
    asset_id: int,
) -> dict:
    """Return upload progress for a job asset."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                job_id,
                asset_type,
                size_bytes,
                uploaded_size_bytes,
                upload_status,
                validation_status
            FROM job_assets
            WHERE id = %s
              AND job_id = %s
            """,
            (asset_id, job_id),
        )
        asset = cursor.fetchone()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload asset not found.",
        )

    expected_size = asset["size_bytes"] or 0
    uploaded_size = asset["uploaded_size_bytes"] or 0

    if asset["upload_status"] in {"VALIDATED", "COMPLETED"}:
        progress_percent = 100
    elif expected_size > 0:
        progress_percent = min(100, round((uploaded_size / expected_size) * 100, 2))
    else:
        progress_percent = 0

    return {
        "assetId": asset["id"],
        "jobId": asset["job_id"],
        "assetType": asset["asset_type"],
        "uploadStatus": asset["upload_status"],
        "validationStatus": asset["validation_status"],
        "expectedSizeBytes": expected_size,
        "uploadedSizeBytes": uploaded_size,
        "progressPercent": progress_percent,
    }
