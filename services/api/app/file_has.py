"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        file_hash.py
Module:      API / Uploads
Description:

Provides SHA-256 hashing helpers for uploaded files.

============================================================================
"""

import hashlib


def create_sha256_hasher() -> "hashlib._Hash":
    """Create a SHA-256 hasher instance."""

    return hashlib.sha256()