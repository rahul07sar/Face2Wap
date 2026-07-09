"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        test_storage_result_integration.py
Module:      API / Storage Integration Tests
Description:

Tests result asset database registration against PostgreSQL while preserving
production data through transaction rollback.

============================================================================
"""

import psycopg

from app.config import settings
from app.storage_result_service import prepare_result_asset


def test_prepare_result_asset_database_registration() -> None:
    """Register a result asset and verify its persisted database fields."""

    connection = psycopg.connect(
        settings.database_url,
        row_factory=psycopg.rows.dict_row,
    )

    try:
        with connection.transaction(force_rollback=True):
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT job_id
                    FROM jobs
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
                job = cursor.fetchone()

            assert job is not None

            result = prepare_result_asset(
                connection,
                job_id=job["job_id"],
                filename="integration-result.png",
                mime_type="image/png",
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        job_id,
                        asset_type,
                        object_path,
                        mime_type,
                        storage_provider,
                        upload_status,
                        validation_status,
                        completed_at
                    FROM job_assets
                    WHERE id = %s
                    """,
                    (result["assetId"],),
                )
                asset = cursor.fetchone()

            assert asset is not None
            assert asset["job_id"] == job["job_id"]
            assert asset["asset_type"] == "RESULT"
            assert asset["mime_type"] == "image/png"
            assert asset["storage_provider"] == "local"
            assert asset["upload_status"] == "COMPLETED"
            assert asset["validation_status"] == "VALIDATED"
            assert asset["completed_at"] is not None

    finally:
        connection.close()
        