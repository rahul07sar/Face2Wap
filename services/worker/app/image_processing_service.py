"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        image_processing_service.py
Module:      Worker / Image Processing
Description:

Coordinates the complete image face-swap worker flow.

The service claims a queued image job, resolves its validated source and target
assets, runs SocAIty/face2face inference, stores and registers the generated
result, updates progress, and records failures safely.

============================================================================
"""

from pathlib import Path
from typing import Optional

import psycopg

from app.face_swap_engine_base import FaceSwapEngineError
from app.face_swap_engine_factory import get_face_swap_engine
from app.socaity_face_swap_engine import (
    ImageFaceSwapError,
    prepare_worker_temp_image_path,
    resolve_worker_upload_path,
)
from app.image_job_service import (
    ImageJobError,
    claim_image_swap_job,
)
from app.result_registry import register_worker_result


# ============================================================================
# Exceptions
# ============================================================================

class ImageProcessingError(RuntimeError):
    """Raised when an image face-swap job cannot be completed."""


# ============================================================================
# Job Status Helpers
# ============================================================================

def _update_job_progress(
    connection: psycopg.Connection,
    *,
    job_id: str,
    progress_percent: int,
) -> None:
    """Persist image-processing progress for an active job."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE jobs
            SET progress_percent = %s,
                updated_at = NOW()
            WHERE job_id = %s
              AND status = 'PROCESSING'
            """,
            (
                progress_percent,
                job_id,
            ),
        )

        if cursor.rowcount != 1:
            raise ImageProcessingError(
                "Image-processing progress could not be updated.",
            )


def _mark_job_failed(
    connection: psycopg.Connection,
    *,
    job_id: str,
    error_message: str,
) -> None:
    """Mark an image-processing job as failed."""

    safe_error_message = (
        error_message.strip()
        or "Image face-swap processing failed."
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE jobs
            SET status = 'FAILED',
                error_message = %s,
                updated_at = NOW()
            WHERE job_id = %s
              AND status IN (
                  'QUEUED',
                  'PROCESSING'
              )
            """,
            (
                safe_error_message[:2000],
                job_id,
            ),
        )


# ============================================================================
# Image Processing
# ============================================================================

def process_image_swap_job(
    connection: psycopg.Connection,
    *,
    job_id: str,
) -> dict:
    """Process one queued image face-swap job from claim through completion."""

    generated_temp_path: Optional[Path] = None

    try:
        claimed_job = claim_image_swap_job(
            connection,
            job_id=job_id,
        )

        connection.commit()

        source_path = resolve_worker_upload_path(
            claimed_job["sourceObjectPath"],
        )

        target_path = resolve_worker_upload_path(
            claimed_job["targetObjectPath"],
        )

        generated_temp_path = prepare_worker_temp_image_path(
            job_id=job_id,
            filename="face2wap-result.png",
        )

        _update_job_progress(
            connection,
            job_id=job_id,
            progress_percent=30,
        )

        connection.commit()

        face_swap_engine = get_face_swap_engine()

        face_swap_engine.swap_image(
            source_path=source_path,
            target_path=target_path,
            output_path=generated_temp_path,
        )

        _update_job_progress(
            connection,
            job_id=job_id,
            progress_percent=80,
        )

        connection.commit()

        result = register_worker_result(
            connection,
            job_id=job_id,
            source_path=generated_temp_path,
            filename="face2wap-result.png",
            mime_type="image/png",
        )

        connection.commit()

        return {
            **result,
            "status": "COMPLETED",
            "progressPercent": 100,
        }

    except (
        FaceSwapEngineError,
        ImageJobError,
        ImageFaceSwapError,
        ImageProcessingError,
        psycopg.Error,
        OSError,
        ValueError,
    ) as error:
        connection.rollback()

        try:
            _mark_job_failed(
                connection,
                job_id=job_id,
                error_message=str(error),
            )

            connection.commit()

        except psycopg.Error:
            connection.rollback()

        raise ImageProcessingError(
            str(error)
            or "Image face-swap processing failed.",
        ) from error

    except Exception as error:
        connection.rollback()

        try:
            _mark_job_failed(
                connection,
                job_id=job_id,
                error_message=(
                    "Unexpected image face-swap processing failure."
                ),
            )

            connection.commit()

        except psycopg.Error:
            connection.rollback()

        raise ImageProcessingError(
            "Unexpected image face-swap processing failure.",
        ) from error

    finally:
        if generated_temp_path is not None:
            generated_temp_path.unlink(
                missing_ok=True,
            )
