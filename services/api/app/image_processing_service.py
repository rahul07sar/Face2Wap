"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        image_processing_service.py
Module:      API / Image Processing
Description:

Validates anonymous image face-swap processing requests, transitions eligible
jobs to QUEUED, and dispatches queued jobs to the protected worker service.

Worker dispatch is designed to run as an API background task so the frontend
does not need to keep the processing request open until inference completes.

============================================================================
"""

from datetime import datetime, timezone
from typing import Any

import httpx
import psycopg
from fastapi import HTTPException, status
from psycopg.rows import dict_row

from app.config import settings
from app.security import verify_job_token


# ============================================================================
# Constants
# ============================================================================

REQUIRED_IMAGE_ASSET_TYPES = {
    "SOURCE_FACE_IMAGE",
    "TARGET_IMAGE",
}


# ============================================================================
# Processing Request Validation
# ============================================================================

def queue_image_swap_job(
    connection: psycopg.Connection,
    *,
    job_id: str,
    job_token: str,
) -> dict:
    """
    Validate and queue an image face-swap job.

    This function commits the QUEUED transition because the worker uses a
    separate PostgreSQL connection and must be able to observe the new state
    before processing begins.
    """

    normalized_job_token = job_token.strip()

    if not normalized_job_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid job token is required.",
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                job_id,
                job_token_hash,
                job_type,
                status,
                expires_at
            FROM jobs
            WHERE job_id = %s
            FOR UPDATE
            """,
            (job_id,),
        )

        job = cursor.fetchone()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )

        if not verify_job_token(
            normalized_job_token,
            job["job_token_hash"],
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid job token.",
            )

        if job["expires_at"] <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Job has expired.",
            )

        if job["job_type"] != "IMAGE_SWAP":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job is not an image face-swap job.",
            )

        if job["status"] == "QUEUED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Image face-swap job is already queued.",
            )

        if job["status"] == "PROCESSING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Image face-swap job is already processing.",
            )

        if job["status"] == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Image face-swap job is already completed.",
            )

        if job["status"] == "EXPIRED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Job has expired.",
            )

        if job["status"] == "BLOCKED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Job is blocked from processing.",
            )

        if job["status"] == "FAILED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Failed image-processing jobs cannot currently be "
                    "re-queued."
                ),
            )

        if job["status"] != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job is not ready to be queued.",
            )

        cursor.execute(
            """
            SELECT
                asset_type,
                upload_status,
                validation_status,
                object_path
            FROM job_assets
            WHERE job_id = %s
              AND asset_type IN (
                  'SOURCE_FACE_IMAGE',
                  'TARGET_IMAGE'
              )
            ORDER BY id ASC
            """,
            (job_id,),
        )

        assets = cursor.fetchall()

        completed_asset_types = {
            asset["asset_type"]
            for asset in assets
            if (
                asset["upload_status"] == "COMPLETED"
                and asset["validation_status"] == "VALIDATED"
                and asset["object_path"]
            )
        }

        missing_asset_types = (
            REQUIRED_IMAGE_ASSET_TYPES
            - completed_asset_types
        )

        if missing_asset_types:
            readable_missing_assets = ", ".join(
                sorted(missing_asset_types),
            )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Job does not have all required validated assets: "
                    f"{readable_missing_assets}."
                ),
            )

        cursor.execute(
            """
            UPDATE jobs
            SET status = 'QUEUED',
                progress_percent = 5,
                error_message = NULL,
                updated_at = NOW()
            WHERE job_id = %s
              AND status = 'PENDING'
            """,
            (job_id,),
        )

        if cursor.rowcount != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Image face-swap job could not be queued.",
            )

    # connection.commit()

    return {
        "jobId": job_id,
        "jobType": "IMAGE_SWAP",
        "status": "QUEUED",
        "progressPercent": 5,
    }


# ============================================================================
# Worker Dispatch Failure Handling
# ============================================================================

def _mark_worker_dispatch_failed(
    *,
    job_id: str,
    error_message: str,
) -> None:
    """
    Mark a job as failed when it could not be delivered to the worker.

    Only jobs that are still QUEUED are updated. A job already claimed by the
    worker remains PROCESSING and is not overwritten by a late HTTP timeout.
    """

    safe_error_message = (
        error_message.strip()
        or "The image-processing worker could not be reached."
    )

    try:
        with psycopg.connect(
            settings.database_url,
            row_factory=dict_row,
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE jobs
                    SET status = 'FAILED',
                        error_message = %s,
                        updated_at = NOW()
                    WHERE job_id = %s
                      AND status = 'QUEUED'
                    """,
                    (
                        safe_error_message[:2000],
                        job_id,
                    ),
                )

            connection.commit()

    except psycopg.Error:
        # The dispatch error must not be hidden by a secondary database error.
        return


# ============================================================================
# Worker Dispatch
# ============================================================================

async def dispatch_image_swap_job(
    *,
    job_id: str,
) -> dict:
    """
    Dispatch one queued image face-swap job to the worker service.

    This function is intended to be registered with FastAPI BackgroundTasks
    after queue_image_swap_job() succeeds.
    """

    worker_base_url = (
        settings.worker_base_url.strip().rstrip("/")
    )

    worker_api_token = (
        settings.worker_api_token.strip()
    )

    if not worker_base_url:
        error_message = (
            "WORKER_BASE_URL is not configured."
        )

        _mark_worker_dispatch_failed(
            job_id=job_id,
            error_message=error_message,
        )

        return {
            "jobId": job_id,
            "status": "FAILED",
            "error": error_message,
        }

    if not worker_api_token:
        error_message = (
            "WORKER_API_TOKEN is not configured."
        )

        _mark_worker_dispatch_failed(
            job_id=job_id,
            error_message=error_message,
        )

        return {
            "jobId": job_id,
            "status": "FAILED",
            "error": error_message,
        }

    worker_url = (
        f"{worker_base_url}"
        f"/internal/jobs/{job_id}/process-image"
    )

    timeout = httpx.Timeout(
        settings.worker_request_timeout_seconds,
        connect=10.0,
    )

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
        ) as client:
            response = await client.post(
                worker_url,
                headers={
                    "X-Worker-Token":
                        worker_api_token,
                    "Accept":
                        "application/json",
                },
            )

    except httpx.TimeoutException:
        error_message = (
            "The image-processing worker request timed out."
        )

        _mark_worker_dispatch_failed(
            job_id=job_id,
            error_message=error_message,
        )

        return {
            "jobId": job_id,
            "status": "FAILED",
            "error": error_message,
        }

    except httpx.HTTPError:
        error_message = (
            "The image-processing worker could not be reached."
        )

        _mark_worker_dispatch_failed(
            job_id=job_id,
            error_message=error_message,
        )

        return {
            "jobId": job_id,
            "status": "FAILED",
            "error": error_message,
        }

    if not response.is_success:
        error_message = _read_worker_error(
            response,
        )

        _mark_worker_dispatch_failed(
            job_id=job_id,
            error_message=error_message,
        )

        return {
            "jobId": job_id,
            "status": "FAILED",
            "error": error_message,
        }

    try:
        worker_result = response.json()
    except ValueError:
        worker_result = {
            "jobId": job_id,
            "status": "COMPLETED",
        }

    return {
        "jobId": job_id,
        "status": worker_result.get(
            "status",
            "COMPLETED",
        ),
        "workerResult": worker_result,
    }


def _read_worker_error(
    response: httpx.Response,
) -> str:
    """Extract a safe error message from a failed worker response."""

    fallback_message = (
        "The image-processing worker rejected the job."
    )

    try:
        payload: Any = response.json()
    except ValueError:
        return fallback_message

    if not isinstance(payload, dict):
        return fallback_message

    detail = payload.get("detail")

    if isinstance(detail, str) and detail.strip():
        return detail.strip()

    return fallback_message
