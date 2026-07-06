"""
Face2Wap Worker Service.

Runs GPU-backed image and video face swap jobs using the
SocAIty/face2face engine and FFmpeg.
"""

from fastapi import FastAPI

app = FastAPI(title="Face2Wap Worker", version="0.1.0")


@app.get("/health")
def health_check():
    """Return worker service health status."""
    return {
        "service": "face2wap-worker",
        "status": "ok",
        "version": "0.1.0",
    }