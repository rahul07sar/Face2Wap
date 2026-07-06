"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        file_metadata.py
Module:      API / Uploads
Description:

Extracts lightweight image/video metadata after upload.

============================================================================
"""

from pathlib import Path


def extract_file_metadata(file_path: Path, mime_type: str) -> dict:
    """
    Extract file metadata.
    """

    return {
        "width": None,
        "height": None,
        "duration_seconds": None,
    }