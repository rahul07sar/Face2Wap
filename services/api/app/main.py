"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        main.py
Module:      API Service
Description:

Initializes the Face2Wap FastAPI API service and exposes health checks plus
open anonymous job APIs.

============================================================================
"""

from datetime import datetime, timedelta, timezone

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status, File, UploadFile
from fastapi.responses import JSONResponse

from app.audit import write_audit_log
from app.config import settings
from app.database import get_connection
from app.rate_limit import enforce_rate_limit, get_client_ip
from app.schemas import (
    CreateJobRequest,
    CreateJobResponse,
    JobResultResponse,
    JobStatusResponse,
)
from app.security import (
    generate_job_id,
    generate_job_token,
    hash_job_token,
    verify_job_token,
)
from app.upload_schemas import PrepareUploadRequest, PrepareUploadResponse
from app.upload_service import prepare_job_upload
from app.upload_handler import upload_job_asset
from app.upload_retry_service import retry_failed_upload
from app.upload_completion_service import complete_validated_upload
from app.upload_progress_service import get_asset_upload_progress
from app.cleanup_service import cleanup_expired_uploads
from app.cleanup_service import (
    cleanup_expired_results,
    cleanup_expired_uploads,
)
from app.orphan_cleanup_service import cleanup_orphan_files
from app.temp_cleanup_service import cleanup_stale_temp_files

# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title="Face2Wap API",
    version="0.2.0",
)


# ============================================================================
# Health Checks
# ============================================================================

@app.get("/health")
def health_check():
    """Return API and PostgreSQL health status."""

    try:
        with psycopg.connect(settings.database_url, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

    except psycopg.Error:
        return JSONResponse(
            status_code=503,
            content={
                "service": "face2wap-api",
                "status": "error",
                "database": "unavailable",
                "version": "0.2.0",
            },
        )

    return {
        "service": "face2wap-api",
        "status": "ok",
        "database": "ok",
        "version": "0.2.0",
    }


# ============================================================================
# Open Job System
# ============================================================================

@app.post(
    "/jobs",
    response_model=CreateJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    payload: CreateJobRequest,
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Create an anonymous Face2Wap job and return its private access token."""

    enforce_rate_limit(connection, request)

    job_id = generate_job_id()
    job_token = generate_job_token()
    job_token_hash = hash_job_token(job_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.job_expiry_hours)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO jobs (
                job_id,
                job_token_hash,
                job_type,
                status,
                progress_percent,
                expires_at
            )
            VALUES (%s, %s, %s, 'PENDING', 0, %s)
            """,
            (
                job_id,
                job_token_hash,
                payload.job_type,
                expires_at,
            ),
        )

    write_audit_log(
        connection,
        action="JOB_CREATED",
        job_id=job_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        metadata={"jobType": payload.job_type},
    )

    connection.commit()

    return {
        "jobId": job_id,
        "jobToken": job_token,
        "status": "PENDING",
        "expiresAt": expires_at,
    }


@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Return public status for an anonymous job."""

    enforce_rate_limit(connection, request)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                job_id,
                job_type,
                status,
                progress_percent,
                error_message,
                expires_at
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,),
        )

        job = cursor.fetchone()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    write_audit_log(
        connection,
        action="JOB_STATUS_VIEWED",
        job_id=job_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    connection.commit()

    return {
        "jobId": job["job_id"],
        "jobType": job["job_type"],
        "status": job["status"],
        "progressPercent": job["progress_percent"],
        "errorMessage": job["error_message"],
        "expiresAt": job["expires_at"],
    }


@app.get("/jobs/{job_id}/result", response_model=JobResultResponse)
def get_job_result(
    job_id: str,
    request: Request,
    token: str = Query(...),
    connection: psycopg.Connection = Depends(get_connection),
):
    """Return the result asset for a completed anonymous job."""

    enforce_rate_limit(connection, request)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                job_id,
                job_token_hash,
                status,
                expires_at
            FROM jobs
            WHERE job_id = %s
            """,
            (job_id,),
        )

        job = cursor.fetchone()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

   if job["expires_at"] <= datetime.now(timezone.utc): 
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Job has expired.",
        )

    if not verify_job_token(token, job["job_token_hash"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid job token.",
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT object_path
            FROM job_assets
            WHERE job_id = %s
              AND asset_type = 'RESULT'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (job_id,),
        )

        result_asset = cursor.fetchone()

    write_audit_log(
        connection,
        action="JOB_RESULT_VIEWED",
        job_id=job_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    connection.commit()

    return {
        "jobId": job_id,
        "status": job["status"],
        "resultUrl": result_asset["object_path"] if result_asset else None,
    }

# ============================================================================
# Upload and Storage System
# ============================================================================

@app.post(
    "/jobs/{job_id}/uploads/prepare",
    response_model=PrepareUploadResponse,
)
def prepare_upload(
    job_id: str,
    payload: PrepareUploadRequest,
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Prepare an upload slot for source image, target image, or target video."""

    enforce_rate_limit(connection, request)

    result = prepare_job_upload(
        connection,
        job_id=job_id,
        asset_type=payload.asset_type,
        filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
    )

    write_audit_log(
        connection,
        action="UPLOAD_PREPARED",
        job_id=job_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        metadata={
            "assetType": payload.asset_type,
            "mimeType": payload.mime_type,
            "sizeBytes": payload.size_bytes,
        },
    )

    connection.commit()
    return result

@app.post("/jobs/{job_id}/assets/{asset_id}/upload")
async def upload_asset(
    job_id: str,
    asset_id: int,
    request: Request,
    file: UploadFile = File(...),
    connection: psycopg.Connection = Depends(get_connection),
):
    """Upload a prepared source image, target image, or target video asset."""

    enforce_rate_limit(connection, request)

    result = await upload_job_asset(
        connection,
        job_id=job_id,
        asset_id=asset_id,
        file=file,
    )

    write_audit_log(
        connection,
        action="ASSET_UPLOADED",
        job_id=job_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        metadata={
            "assetId": asset_id,
            "assetType": result["assetType"],
            "sizeBytes": result["sizeBytes"],
            "sha256": result["sha256"],
        },
    )

    connection.commit()
    return result

# ============================================================================
# Upload and Storage System failures
# ============================================================================

@app.post("/jobs/{job_id}/assets/{asset_id}/retry")
def retry_asset_upload(
    job_id: str,
    asset_id: int,
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Reset a failed upload asset so it can be uploaded again."""

    enforce_rate_limit(connection, request)

    result = retry_failed_upload(
        connection,
        job_id=job_id,
        asset_id=asset_id,
    )

    write_audit_log(
        connection,
        action="UPLOAD_RETRY_PREPARED",
        job_id=job_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        metadata={
            "assetId": asset_id,
            "assetType": result["assetType"],
        },
    )

    connection.commit()
    return result

# ============================================================================
# Upload validation for queuing
# ============================================================================

@app.post("/jobs/{job_id}/assets/{asset_id}/complete")
def complete_asset_upload(
    job_id: str,
    asset_id: int,
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Complete a validated upload asset."""

    enforce_rate_limit(connection, request)

    result = complete_validated_upload(
        connection,
        job_id=job_id,
        asset_id=asset_id,
    )

    write_audit_log(
        connection,
        action="UPLOAD_COMPLETED",
        job_id=job_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        metadata={
            "assetId": asset_id,
            "assetType": result["assetType"],
            "jobReadyForQueue": result["jobReadyForQueue"],
        },
    )

    connection.commit()
    return result

# ============================================================================
# Upload Storage Progress
# ============================================================================

@app.get("/jobs/{job_id}/assets/{asset_id}/progress")
def get_upload_progress(
    job_id: str,
    asset_id: int,
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Return upload progress for a prepared/uploading/validated asset."""

    enforce_rate_limit(connection, request)

    return get_asset_upload_progress(
        connection,
        job_id=job_id,
        asset_id=asset_id,
    )

# ============================================================================
# Upload expiry cleanup
# ============================================================================

@app.post("/cleanup/uploads/expired")
def cleanup_expired_upload_assets(
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Clean expired prepared/failed upload assets."""

    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cleanup endpoint is only available in development.",
        )

    enforce_rate_limit(connection, request)

    return cleanup_expired_uploads(connection)

# ============================================================================
# Results expiry cleanup
# ============================================================================

@app.post("/cleanup/results/expired")
def cleanup_expired_result_assets(
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Clean result assets belonging to expired jobs."""

    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cleanup endpoint is only available in development.",
        )

    enforce_rate_limit(connection, request)

    return cleanup_expired_results(connection)

# ============================================================================
# Orphaned or Unidentified file cleanup
# ============================================================================

@app.post("/cleanup/orphans")
def cleanup_orphan_storage_files(
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Clean local storage files that are not referenced by job_assets."""

    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cleanup endpoint is only available in development.",
        )

    enforce_rate_limit(connection, request)

    return cleanup_orphan_files(connection)

# ============================================================================
# Stale temporary file cleanup
# ============================================================================

@app.post("/cleanup/temp")
def cleanup_stale_temporary_files(
    request: Request,
    connection: psycopg.Connection = Depends(get_connection),
):
    """Clean stale files from local temporary storage."""

    if settings.app_env != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cleanup endpoint is only available in development.",
        )

    enforce_rate_limit(connection, request)

    return cleanup_stale_temp_files()
