"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        file_metadata.py
Module:      API / Uploads
Description:

Extracts lightweight image and video metadata after upload. Image metadata is
read locally using Pillow. Video metadata is read using FFprobe.

============================================================================
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

FFPROBE_TIMEOUT_SECONDS = 15


def extract_image_metadata(file_path: Path) -> dict[str, Any]:
    """Extract width and height from an uploaded image file."""

    try:
        with Image.open(file_path) as image:
            width, height = image.size

        return {
            "width": width,
            "height": height,
            "duration_seconds": None,
        }

    except UnidentifiedImageError as error:
        raise ValueError("Uploaded image file could not be identified.") from error


def extract_video_metadata(file_path: Path) -> dict[str, Any]:
    """Extract width, height, and duration from an uploaded video file."""

    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,duration",
        "-of",
        "json",
        str(file_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True,
            timeout=FFPROBE_TIMEOUT_SECONDS,
        )

        payload = json.loads(result.stdout)
        streams = payload.get("streams", [])

        if not streams:
            raise ValueError("Uploaded video does not contain a video stream.")

        stream = streams[0]

        return {
            "width": int(stream["width"]) if stream.get("width") else None,
            "height": int(stream["height"]) if stream.get("height") else None,
            "duration_seconds": (
                float(stream["duration"]) if stream.get("duration") else None
            ),
        }

    except subprocess.TimeoutExpired as error:
        raise ValueError("Video metadata extraction timed out.") from error

    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("Uploaded video metadata could not be extracted.") from error


def extract_file_metadata(file_path: Path, mime_type: str) -> dict[str, Any]:
    """Extract metadata based on the uploaded file MIME type."""

    if mime_type in IMAGE_MIME_TYPES:
        return extract_image_metadata(file_path)

    if mime_type.startswith("video/"):
        return extract_video_metadata(file_path)

    return {
        "width": None,
        "height": None,
        "duration_seconds": None,
    }
