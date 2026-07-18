"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        video_processing_service.py
Module:      Worker / Video Processing
Description:

Coordinates the complete video face-swap worker flow.

This service claims a queued video job, resolves its validated source image
and target video, executes the configured face-swap engine, stores and
registers the generated video, updates job progress, and records failures
safely.

============================================================================
"""

from pathlib import Path
from typing import Optional

import psycopg

from app.api_transfer_client import (
    WorkerApiTransferError,
    download_worker_asset,
    upload_worker_result,
)
from app.config import settings
from app.face_swap_engine_base import FaceSwapEngineError
from app.face_swap_engine_factory import get_face_swap_engine
from app.socaity_face_swap_engine import (
    ImageFaceSwapError,
)
from app.video_job_service import (
    VideoJobError,
    claim_video_swap_job,
)
from app.job_progress_heartbeat import (
    JobProgressHeartbeat,
)


# ============================================================================
# Exceptions
# ============================================================================

class VideoProcessingError(RuntimeError):
    """Raised when a video face-swap job cannot be completed."""


# ============================================================================
# Temporary Path Handling
# ============================================================================

def _resolve_under_root(
    root: str,
    object_path: str,
) -> Path:
    """Resolve an object path safely under a configured storage root."""

    storage_root = Path(root).resolve()
    resolved_path = (
        storage_root
        / object_path
    ).resolve()

    if (
        storage_root not in resolved_path.parents
        and resolved_path != storage_root
    ):
        raise VideoProcessingError(
            "Resolved video path escaped its configured storage root.",
        )

    return resolved_path


def prepare_worker_temp_video_path(
    *,
    job_id: str,
    filename: str,
) -> Path:
    """Prepare a safe temporary output path for a video face-swap job."""

    normalized_job_id = job_id.strip()

    if not normalized_job_id:
        raise VideoProcessingError(
            "A job ID is required to prepare the video result path.",
        )

    safe_filename = Path(
        filename,
    ).name

    if not safe_filename:
        raise VideoProcessingError(
            "A result filename is required.",
        )

    file_extension = Path(
        safe_filename,
    ).suffix.lower()

    if file_extension not in {
        ".mp4",
        ".mov",
        ".webm",
        ".mkv",
    }:
        raise VideoProcessingError(
            "Video results must use MP4, MOV, WebM, or MKV.",
        )

    object_path = (
        f"{normalized_job_id}/"
        f"{safe_filename}"
    )

    temp_path = _resolve_under_root(
        settings.local_temp_dir,
        object_path,
    )

    temp_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return temp_path


# ============================================================================
# Job Status Helpers
# ============================================================================

def _update_job_progress(
    connection: psycopg.Connection,
    *,
    job_id: str,
    progress_percent: int,
) -> None:
    """Persist video-processing progress for an active job."""

    normalized_progress = max(
        0,
        min(
            100,
            int(progress_percent),
        ),
    )

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
                normalized_progress,
                job_id,
            ),
        )

        if cursor.rowcount != 1:
            raise VideoProcessingError(
                "Video-processing progress could not be updated.",
            )


def _mark_job_failed(
    connection: psycopg.Connection,
    *,
    job_id: str,
    error_message: str,
) -> None:
    """Mark a queued or processing video job as failed."""

    safe_error_message = (
        error_message.strip()
        or "Video face-swap processing failed."
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
# Video Processing
# ============================================================================

def process_video_swap_job(
    connection: psycopg.Connection,
    *,
    job_id: str,
) -> dict:
    """Process one queued video face-swap job through completion."""

    generated_video_path: Optional[Path] = None
    source_path: Optional[Path] = None
    target_path: Optional[Path] = None
    processing_heartbeat: Optional[JobProgressHeartbeat] = None

    try:
        claimed_job = claim_video_swap_job(
            connection,
            job_id=job_id,
        )

        connection.commit()

        source_path = download_worker_asset(
            job_id=job_id,
            asset_id=claimed_job["sourceAssetId"],
            filename=Path(
                claimed_job["sourceObjectPath"],
            ).name,
        )

        target_path = download_worker_asset(
            job_id=job_id,
            asset_id=claimed_job["targetAssetId"],
            filename=Path(
                claimed_job["targetObjectPath"],
            ).name,
        )

        generated_video_path = (
            prepare_worker_temp_video_path(
                job_id=job_id,
                filename="face2wap-result.mp4",
            )
        )

        _update_job_progress(
            connection,
            job_id=job_id,
            progress_percent=20,
        )

        connection.commit()

        face_swap_engine = (
            get_face_swap_engine()
        )
        processing_heartbeat = JobProgressHeartbeat(
            job_id=job_id,
            start_progress=20,
            max_progress=98,
            total_window_seconds=(
                settings
                .facefusion_video_process_timeout_seconds
            ),
        )
        processing_heartbeat.start()

        face_swap_engine.swap_video(
            source_path=source_path,
            target_path=target_path,
            output_path=generated_video_path,
        )

        processing_heartbeat.stop()
        processing_heartbeat = None

        _update_job_progress(
            connection,
            job_id=job_id,
            progress_percent=99,
        )

        connection.commit()

        result = upload_worker_result(
            job_id=job_id,
            result_path=generated_video_path,
            filename="face2wap-result.mp4",
            mime_type="video/mp4",
        )

        return {
            **result,
            "status": "COMPLETED",
            "progressPercent": 100,
        }

    except (
        FaceSwapEngineError,
        ImageFaceSwapError,
        VideoJobError,
        VideoProcessingError,
        WorkerApiTransferError,
        psycopg.Error,
        OSError,
        ValueError,
    ) as error:
        connection.rollback()

        if processing_heartbeat is not None:
            processing_heartbeat.stop()
            processing_heartbeat = None

        try:
            _mark_job_failed(
                connection,
                job_id=job_id,
                error_message=str(error),
            )

            connection.commit()

        except psycopg.Error:
            connection.rollback()

        raise VideoProcessingError(
            str(error)
            or "Video face-swap processing failed.",
        ) from error

    except Exception as error:
        connection.rollback()

        if processing_heartbeat is not None:
            processing_heartbeat.stop()
            processing_heartbeat = None

        try:
            _mark_job_failed(
                connection,
                job_id=job_id,
                error_message=(
                    "Unexpected video face-swap processing failure."
                ),
            )

            connection.commit()

        except psycopg.Error:
            connection.rollback()

        raise VideoProcessingError(
            "Unexpected video face-swap processing failure.",
        ) from error

    finally:
        if processing_heartbeat is not None:
            processing_heartbeat.stop()

        if source_path is not None:
            source_path.unlink(
                missing_ok=True,
            )

        if target_path is not None:
            target_path.unlink(
                missing_ok=True,
            )

        if generated_video_path is not None:
            generated_video_path.unlink(
                missing_ok=True,
            )
