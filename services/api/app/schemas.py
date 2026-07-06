"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        schemas.py
Module:      API / Schemas
Description:

Defines request and response schemas for the open anonymous job system.

============================================================================
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


JobType = Literal["IMAGE_SWAP", "VIDEO_SWAP"]


class CreateJobRequest(BaseModel):
    """Request body for creating an anonymous job."""

    job_type: JobType = Field(..., alias="jobType")


class CreateJobResponse(BaseModel):
    """Response returned after creating an anonymous job."""

    job_id: str = Field(..., alias="jobId")
    job_token: str = Field(..., alias="jobToken")
    status: str
    expires_at: datetime = Field(..., alias="expiresAt")


class JobStatusResponse(BaseModel):
    """Public job status response."""

    job_id: str = Field(..., alias="jobId")
    job_type: str = Field(..., alias="jobType")
    status: str
    progress_percent: int = Field(..., alias="progressPercent")
    error_message: str | None = Field(None, alias="errorMessage")
    expires_at: datetime = Field(..., alias="expiresAt")


class JobResultResponse(BaseModel):
    """Job result response."""

    job_id: str = Field(..., alias="jobId")
    status: str
    result_url: str | None = Field(None, alias="resultUrl")