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

from datetime import UTC, datetime, timedelta

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
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
    expires_at = datetime.now(UTC) + timedelta(hours=settings.job_expiry_hours)

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

    if job["expires_at"] <= datetime.now(UTC):
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