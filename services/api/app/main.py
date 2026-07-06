"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        main.py
Module:      API Service
Description:

Initializes the Face2Wap FastAPI service and exposes application health
checks, including PostgreSQL database connectivity verification.

============================================================================
"""

import os

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse


# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title="Face2Wap API",
    version="0.1.0",
)


# ============================================================================
# Health Checks
# ============================================================================

@app.get("/health")
def health_check():
    """
    Return API and PostgreSQL health status.

    The endpoint fails closed with HTTP 503 when the database cannot be
    reached or the connectivity check fails.
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        return JSONResponse(
            status_code=503,
            content={
                "service": "face2wap-api",
                "status": "error",
                "database": "configuration_missing",
                "version": "0.1.0",
            },
        )

    try:
        with psycopg.connect(database_url, connect_timeout=5) as connection:
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
                "version": "0.1.0",
            },
        )

    return {
        "service": "face2wap-api",
        "status": "ok",
        "database": "ok",
        "version": "0.1.0",
    }