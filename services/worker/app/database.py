"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        database.py
Module:      Worker / Database
Description:

Provides PostgreSQL connection helpers for worker-side job and result updates.

============================================================================
"""

from collections.abc import Generator

import psycopg
from psycopg.rows import dict_row

from app.config import settings


def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Create a PostgreSQL connection for one worker unit of work."""

    with psycopg.connect(
        settings.database_url,
        row_factory=dict_row,
        connect_timeout=5,
    ) as connection:
        yield connection
