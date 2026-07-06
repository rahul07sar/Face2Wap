"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        upload_validation.py
Module:      API / Upload Validation
Description:

Validates upload asset types, MIME types, file sizes, and job compatibility
for image and video face swap workflows.

============================================================================
"""

from fastapi import HTTPException, status

from app.config import settings


IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
}

ASSET_TYPES = {
    "SOURCE_FACE_IMAGE",
    "TARGET_IMAGE",
    "TARGET_VIDEO",
}


def validate_upload_request(
    *,
    job_type: str,
    asset_type: str,
    mime_type: str,
    size_bytes: int,
) -> None:
    """Validate upload request metadata before creating an upload slot."""

    if asset_type not in ASSET_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported asset type.",
        )

    if size_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be greater than zero.",
        )

    max_image_bytes = settings.max_image_size_mb * 1024 * 1024
    max_video_bytes = settings.max_video_size_mb * 1024 * 1024

    if asset_type in {"SOURCE_FACE_IMAGE", "TARGET_IMAGE"}:
        if mime_type not in IMAGE_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported image type.",
            )

        if size_bytes > max_image_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image file is too large.",
            )

    if asset_type == "TARGET_VIDEO":
        if mime_type not in VIDEO_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported video type.",
            )

        if size_bytes > max_video_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Video file is too large.",
            )

    if job_type == "IMAGE_SWAP" and asset_type == "TARGET_VIDEO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image swap jobs cannot use target video uploads.",
        )
    