"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        internal_worker_auth.py
Module:      API / Internal Worker Auth
Description:

Verifies the shared worker API token used for private API-to-worker and
worker-to-API communication.

============================================================================
"""

from secrets import compare_digest

from fastapi import Header, HTTPException, status

from app.config import settings


def verify_internal_worker_token(
    worker_api_token: str = Header(
        ...,
        alias="X-Worker-Token",
    ),
) -> None:
    """Verify the shared private token used by the worker."""

    configured_token = settings.worker_api_token.strip()
    supplied_token = worker_api_token.strip()

    if (
        not configured_token
        or not supplied_token
        or not compare_digest(
            supplied_token,
            configured_token,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid worker API token.",
        )
