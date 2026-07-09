"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        test_result_registry_integration.py
Module:      Worker / Result Registry Tests
Description:

Tests worker result registration against PostgreSQL using transaction rollback
so production-like data is verified without persisting test rows.

============================================================================
"""

from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.config import settings
from app.result_registry import register_worker_result


def test_register_worker_result_database_registration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Register a generated result asset and mark its job completed."""

    monkeypatch.setattr(settings, "local_result_dir", str(tmp_path))

    connection = psycopg.connect(
        settings.database_url,
        row_factory=dict_row,
    )

    generated_file = tmp_path / "generated-result.png"
    generated_file.write_bytes(b"face2wap-worker-generated-result")

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

            result = register_worker_result(
                connection,
                job_id=job["job_id"],
                source_path=generated_file,
                filename="result.png",
                mime_type="image/png",
            )

            assert result["assetType"] == "RESULT"
            assert result["storageProvider"] == "local"
            assert result["objectPath"] == f"{job['job_id']}/result.png"

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        asset_type,
                        object_path,
                        mime_type,
                        storage_provider,
                        upload_status,
                        validation_status
                    FROM job_assets
                    WHERE id = %s
                    """,
                    (result["assetId"],),
                )
                asset = cursor.fetchone()

            assert asset is not None
            assert asset["asset_type"] == "RESULT"
            assert asset["mime_type"] == "image/png"
            assert asset["storage_provider"] == "local"
            assert asset["upload_status"] == "COMPLETED"
            assert asset["validation_status"] == "VALIDATED"

    finally:
        connection.close()
