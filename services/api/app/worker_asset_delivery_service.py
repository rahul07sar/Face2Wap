"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        worker_asset_delivery_service.py
Module:      API / Worker Asset Delivery
Description:

Loads validated upload assets so a remote worker can fetch source and target
files from the API when the worker does not share the API host filesystem.

============================================================================
"""

from pathlib import Path

import psycopg
from fastapi import HTTPException, status

from app.storage.local_file_service import resolve_local_upload_file


def get_worker_download_asset(
    connection: psycopg.Connection,
    *,
    job_id: str,
    asset_id: int,
) -> dict:
    """Return one validated upload asset for remote worker download."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                job_id,
                asset_type,
                object_path,
                mime_type,
                original_filename,
                storage_provider,
                upload_status,
                validation_status
            FROM job_assets
            WHERE id = %s
              AND job_id = %s
            """,
            (
                asset_id,
                job_id,
            ),
        )
        asset = cursor.fetchone()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker asset was not found.",
        )

    if asset["asset_type"] == "RESULT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Result assets cannot be fetched as worker inputs.",
        )

    if asset["storage_provider"] != "local":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Worker asset delivery is unavailable for this storage provider.",
        )

    if asset["upload_status"] != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker asset is not ready for download.",
        )

    if asset["validation_status"] != "VALIDATED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker asset validation is not complete.",
        )

    try:
        file_path = resolve_local_upload_file(
            asset["object_path"],
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker asset file was not found.",
        ) from error

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker asset file was not found.",
        )

    return {
        "assetId": asset["id"],
        "jobId": asset["job_id"],
        "assetType": asset["asset_type"],
        "mimeType": asset["mime_type"] or "application/octet-stream",
        "filename": (
            asset["original_filename"]
            or Path(asset["object_path"]).name
        ),
        "filePath": file_path,
    }
