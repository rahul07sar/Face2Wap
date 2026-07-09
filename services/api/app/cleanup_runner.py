"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        cleanup_runner.py
Module:      API / Cleanup
Description:

Coordinates expired upload, expired result, orphan storage, and stale
temporary file cleanup operations.

============================================================================
"""

import psycopg

from app.cleanup_service import (
    cleanup_expired_results,
    cleanup_expired_uploads,
)
from app.orphan_cleanup_service import cleanup_orphan_files
from app.temp_cleanup_service import cleanup_stale_temp_files


def run_cleanup(connection: psycopg.Connection) -> dict:
    """Run all configured Face2Wap cleanup operations."""

    expired_uploads = cleanup_expired_uploads(connection)
    expired_results = cleanup_expired_results(connection)
    orphan_files = cleanup_orphan_files(connection)
    temp_files = cleanup_stale_temp_files()

    return {
        "expiredUploads": expired_uploads,
        "expiredResults": expired_results,
        "orphanFiles": orphan_files,
        "tempFiles": temp_files,
    }
