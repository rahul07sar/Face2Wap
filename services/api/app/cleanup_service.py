"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        cleanup_service.py
Module:      API / Cleanup
Description:

Cleans expired prepared/failed upload assets and removes their local files
when applicable.

============================================================================
"""

import psycopg

from app.config import settings
from app.storage.factory import get_storage_provider


CLEANABLE_UPLOAD_STATUSES = {
    "PREPARED",
    "FAILED",
}


def cleanup_expired_uploads(connection: psycopg.Connection) -> dict:
    """Delete expired upload files and mark expired upload assets."""

    storage = get_storage_provider()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                job_id,
                object_path,
                storage_provider,
                upload_status
            FROM job_assets
            WHERE upload_expires_at IS NOT NULL
              AND upload_expires_at < NOW()
              AND upload_status = ANY(%s)
            ORDER BY upload_expires_at ASC
            LIMIT %s
            """,
            (
                list(CLEANABLE_UPLOAD_STATUSES),
                settings.cleanup_batch_size,
            ),
        )
        assets = cursor.fetchall()

    deleted_files = 0

    for asset in assets:
        if asset["storage_provider"] == "local":
            if storage.delete_file(
                object_path=asset["object_path"],
                is_result=False,
            ):
                deleted_files += 1

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE job_assets
                SET upload_status = 'EXPIRED',
                    validation_status = 'EXPIRED',
                    updated_at = NOW()
                WHERE id = %s
                """,
                (asset["id"],),
            )

    connection.commit()

    return {
        "expiredAssets": len(assets),
        "deletedFiles": deleted_files,
    }

def cleanup_expired_results(connection: psycopg.Connection) -> dict:
    """Delete result files for expired jobs and mark result assets expired."""

    storage = get_storage_provider()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ja.id,
                ja.job_id,
                ja.object_path,
                ja.storage_provider
            FROM job_assets ja
            JOIN jobs j ON j.job_id = ja.job_id
            WHERE ja.asset_type = 'RESULT'
              AND ja.upload_status = 'COMPLETED'
              AND j.expires_at < NOW()
            ORDER BY j.expires_at ASC
            LIMIT %s
            """,
            (settings.cleanup_batch_size,),
        )
        assets = cursor.fetchall()

    deleted_files = 0

    for asset in assets:
        if asset["storage_provider"] == "local":
            if storage.delete_file(
                object_path=asset["object_path"],
                is_result=True,
            ):
                deleted_files += 1

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE job_assets
                SET upload_status = 'EXPIRED',
                    validation_status = 'EXPIRED',
                    updated_at = NOW()
                WHERE id = %s
                """,
                (asset["id"],),
            )

    connection.commit()

    return {
        "expiredResults": len(assets),
        "deletedFiles": deleted_files,
    }
