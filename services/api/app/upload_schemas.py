"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        upload_schemas.py
Module:      API / Upload Schemas
Description:

Defines request and response schemas for upload preparation.

============================================================================
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AssetType = Literal["SOURCE_FACE_IMAGE", "TARGET_IMAGE", "TARGET_VIDEO"]


class PrepareUploadRequest(BaseModel):
    """Request body for preparing an upload slot."""

    asset_type: AssetType = Field(..., alias="assetType")
    filename: str
    mime_type: str = Field(..., alias="mimeType")
    size_bytes: int = Field(..., alias="sizeBytes")


class PrepareUploadResponse(BaseModel):
    """Response returned after preparing an upload slot."""

    asset_id: int = Field(..., alias="assetId")
    upload_url: str = Field(..., alias="uploadUrl")
    object_path: str = Field(..., alias="objectPath")
    storage_provider: str = Field(..., alias="storageProvider")
    upload_expires_at: datetime = Field(..., alias="uploadExpiresAt")
    