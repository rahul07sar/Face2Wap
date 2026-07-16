"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        rate_limit.py
Module:      API / Rate Limiting
Description:

Provides basic PostgreSQL-backed IP rate limiting for open anonymous API
access.

============================================================================
"""

import psycopg
from fastapi import HTTPException, Request, status

from app.config import settings


def get_client_ip(request: Request) -> str:
    """Resolve client IP address from proxy headers or socket metadata."""

    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def enforce_rate_limit(connection: psycopg.Connection, request: Request) -> None:
    """Enforce a simple fixed-window rate limit by client IP."""
    enforce_scoped_rate_limit(
        connection,
        request,
    )


def enforce_scoped_rate_limit(
    connection: psycopg.Connection,
    request: Request,
    *,
    scope: str = "default",
    max_requests: int | None = None,
) -> None:
    """Enforce a simple fixed-window rate limit by client IP and scope."""

    client_ip = get_client_ip(request)
    normalized_scope = scope.strip() or "default"
    allowed_requests = (
        max_requests
        if max_requests is not None
        else settings.rate_limit_max_requests
    )
    rate_key = f"ip:{client_ip}:{normalized_scope}"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO rate_limits (
                rate_key,
                window_start,
                request_count
            )
            VALUES (%s, NOW(), 1)
            ON CONFLICT (rate_key)
            DO UPDATE SET
                request_count = CASE
                    WHEN rate_limits.window_start
                        < NOW() - (%s * INTERVAL '1 second')
                    THEN 1
                    ELSE rate_limits.request_count + 1
                END,
                window_start = CASE
                    WHEN rate_limits.window_start
                        < NOW() - (%s * INTERVAL '1 second')
                    THEN NOW()
                    ELSE rate_limits.window_start
                END,
                updated_at = NOW()
            RETURNING request_count
            """,
            (
                rate_key,
                settings.rate_limit_window_seconds,
                settings.rate_limit_window_seconds,
            ),
        )

        result = cursor.fetchone()

    request_count = result["request_count"]

    if request_count > allowed_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
