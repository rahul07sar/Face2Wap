"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        orphan_cleanup_service.py
Module:      API / Cleanup
Description:

Finds and deletes orphaned/unidentified local storage files that no longer have matching
job_assets records in PostgreSQL.

============================================================================
"""

from pathlib import Path

import psycopg

from app.config import settings


def cleanup_orphan_files(connection: psycopg.Connection) -> dict:
    """Delete upload/result files that are not referenced by job_assets."""

    upload_result = _cleanup_orphans_under_root(
        connection,
        root_dir=settings.local_upload_dir,
        is_result=False,
    )

    result_result = _cleanup_orphans_under_root(
        connection,
        root_dir=settings.local_result_dir,
        is_result=True,
    )

    return {
        "deletedUploadOrphans": upload_result["deletedFiles"],
        "deletedResultOrphans": result_result["deletedFiles"],
    }


def _cleanup_orphans_under_root(
    connection: psycopg.Connection,
    *,
    root_dir: str,
    is_result: bool,
) -> dict:
    """Delete orphan files below one local storage root."""

    root_path = Path(root_dir).resolve()

    if not root_path.exists():
        return {"deletedFiles": 0}

    deleted_files = 0

    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue

        object_path = str(file_path.resolve().relative_to(root_path))

        if not _asset_object_exists(
            connection,
            object_path=object_path,
            is_result=is_result,
        ):
            file_path.unlink()
            deleted_files += 1

    return {"deletedFiles": deleted_files}


def _asset_object_exists(
    connection: psycopg.Connection,
    *,
    object_path: str,
    is_result: bool,
) -> bool:
    """Return whether a storage object is referenced by job_assets."""

    if is_result:
        asset_type_filter = "asset_type = 'RESULT'"
    else:
        asset_type_filter = "asset_type <> 'RESULT'"

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT 1
            FROM job_assets
            WHERE object_path = %s
              AND {asset_type_filter}
            LIMIT 1
            """,
            (object_path,),
        )

        return cursor.fetchone() is not None
    