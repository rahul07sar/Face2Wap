"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        security.py
Module:      API / Security
Description:

Generates anonymous job identifiers, private job tokens, and secure token
hashes for open job access.

============================================================================
"""

import hashlib
import hmac
import secrets

from app.config import settings


def generate_job_id() -> str:
    """Generate a public anonymous job identifier."""

    return f"job_{secrets.token_urlsafe(24)}"


def generate_job_token() -> str:
    """Generate a private job access token."""

    return secrets.token_urlsafe(48)


def hash_job_token(job_token: str) -> str:
    """Hash a job token using HMAC-SHA256."""

    return hmac.new(
        settings.job_token_secret.encode("utf-8"),
        job_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_job_token(job_token: str, expected_hash: str) -> bool:
    """Verify a job token using constant-time comparison."""

    actual_hash = hash_job_token(job_token)
    return hmac.compare_digest(actual_hash, expected_hash)