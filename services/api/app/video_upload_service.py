"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        video_upload_service.py
Module:      API / Video Upload Service
Description:

Maintains the dedicated target-video upload table that extends generic
job_assets rows with video-specific metadata.

============================================================================
"""

import psycopg


def create_video_upload_record(
    connection: psycopg.Connection,
    *,
    asset_id: int,
    job_id: str,
    object_path: str,
    mime_type: str,
    original_filename: str,
    size_bytes: int,
) -> None:
    """Create or refresh the dedicated row for one target-video asset."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO job_video_uploads (
                asset_id,
                job_id,
                object_path,
                mime_type,
                original_filename,
                size_bytes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (asset_id) DO UPDATE
            SET job_id = EXCLUDED.job_id,
                object_path = EXCLUDED.object_path,
                mime_type = EXCLUDED.mime_type,
                original_filename = EXCLUDED.original_filename,
                size_bytes = EXCLUDED.size_bytes,
                updated_at = NOW()
            """,
            (
                asset_id,
                job_id,
                object_path,
                mime_type,
                original_filename,
                size_bytes,
            ),
        )


def update_video_upload_metadata(
    connection: psycopg.Connection,
    *,
    asset_id: int,
    width: int | None,
    height: int | None,
    duration_seconds: float | None,
) -> None:
    """Persist extracted metadata for one validated target-video upload."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE job_video_uploads
            SET width = %s,
                height = %s,
                duration_seconds = %s,
                updated_at = NOW()
            WHERE asset_id = %s
            """,
            (
                width,
                height,
                duration_seconds,
                asset_id,
            ),
        )


def reset_video_upload_metadata(
    connection: psycopg.Connection,
    *,
    asset_id: int,
) -> None:
    """Clear extracted metadata before retrying a failed target-video upload."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE job_video_uploads
            SET width = NULL,
                height = NULL,
                duration_seconds = NULL,
                updated_at = NOW()
            WHERE asset_id = %s
            """,
            (asset_id,),
        )
