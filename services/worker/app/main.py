"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        main.py
Module:      Worker Service
Description:

Initializes the Face2Wap worker service, exposes worker health checks, and
provides protected internal endpoints for image and video face-swap jobs.

============================================================================
"""

from secrets import compare_digest

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, status

from app.config import settings
from app.database import get_connection
from app.image_processing_service import (
    ImageProcessingError,
    process_image_swap_job,
)
from app.video_processing_service import (
    VideoProcessingError,
    process_video_swap_job,
)

# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title="Face2Wap Worker",
    version="0.2.0",
)


# ============================================================================
# Internal Worker Security
# ============================================================================

def verify_worker_api_token(
    worker_api_token: str = Header(
        ...,
        alias="X-Worker-Token",
    ),
) -> None:
    """Verify the private token used for API-to-worker communication."""

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


# ============================================================================
# Health Checks
# ============================================================================

@app.get("/health")
def health_check():
    """Return worker service health status."""

    return {
        "service": "face2wap-worker",
        "status": "ok",
        "version": "0.2.0",
    }


# ============================================================================
# Image Face-Swap Processing
# ============================================================================

@app.post(
    "/internal/jobs/{job_id}/process-image",
    dependencies=[
        Depends(verify_worker_api_token),
    ],
)
def process_image_job(
    job_id: str,
    connection: psycopg.Connection = Depends(
        get_connection,
    ),
):
    """Process one queued image face-swap job."""

    try:
        return process_image_swap_job(
            connection,
            job_id=job_id,
        )

    except ImageProcessingError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

# ============================================================================
# Video Face-Swap Processing
# ============================================================================

@app.post(
    "/internal/jobs/{job_id}/process-video",
    dependencies=[
        Depends(verify_worker_api_token),
    ],
)
def process_video_job(
    job_id: str,
    connection: psycopg.Connection = Depends(
        get_connection,
    ),
):
    """Process one queued video face-swap job."""

    try:
        return process_video_swap_job(
            connection,
            job_id=job_id,
        )

    except VideoProcessingError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    