"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        audit.py
Module:      API / Audit
Description:

Writes audit events for anonymous job actions.

============================================================================
"""

import json 
from typing import Any

import psycopg


def write_audit_log(
    connection: psycopg.Connection,
    *,
    action: str,
    job_id: str | None,
    ip_address: str | None,
    user_agent: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Persist an audit log entry."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO audit_logs (
                job_id,
                action,
                ip_address,
                user_agent,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s::jsonb)
            """,
            (
                job_id,
                action,
                ip_address,
                user_agent,
                json.dumps(metadata or {}),
            ),
        )