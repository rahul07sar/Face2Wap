"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        main.py
Module:      Worker Service
Description:

Initializes the Face2Wap worker service. The worker will run image and video
face swap jobs using SocAIty/face2face and FFmpeg.

============================================================================
"""

from fastapi import FastAPI


# ============================================================================
# Application
# ============================================================================

app = FastAPI(
    title="Face2Wap Worker",
    version="0.1.0",
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
        "version": "0.1.0",
    }
