"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        job_progress_heartbeat.py
Module:      Worker / Progress Tracking
Description:

Provides a lightweight background heartbeat that keeps job progress moving
while a long-running face-swap engine call is still executing.

============================================================================
"""

import logging
import threading

import psycopg

from app.config import settings


logger = logging.getLogger(__name__)


class JobProgressHeartbeat:
    """Advance a processing job gradually until the active step finishes."""

    def __init__(
        self,
        *,
        job_id: str,
        start_progress: int,
        max_progress: int,
        total_window_seconds: int,
    ) -> None:
        self._job_id = job_id
        self._current_progress = max(
            0,
            min(
                100,
                int(start_progress),
            ),
        )
        self._max_progress = max(
            self._current_progress,
            min(
                99,
                int(max_progress),
            ),
        )
        remaining_steps = max(
            1,
            self._max_progress - self._current_progress,
        )
        self._step_interval_seconds = max(
            5.0,
            float(total_window_seconds) / remaining_steps,
        )
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name=f"job-progress-heartbeat-{job_id}",
            daemon=True,
        )

    def start(self) -> None:
        """Begin the background progress heartbeat."""

        if self._current_progress >= self._max_progress:
            return

        self._thread.start()

    def stop(self) -> None:
        """Stop the heartbeat and wait briefly for it to exit."""

        self._stop_event.set()

        if self._thread.is_alive():
            self._thread.join(
                timeout=2.0,
            )

    def _run(self) -> None:
        """Persist gradual progress updates until stopped or capped."""

        next_progress = self._current_progress + 1

        while (
            next_progress <= self._max_progress
            and not self._stop_event.wait(
                self._step_interval_seconds,
            )
        ):
            try:
                self._write_progress(
                    progress_percent=next_progress,
                )
                self._current_progress = next_progress
                next_progress += 1

            except psycopg.Error:
                logger.warning(
                    "Job progress heartbeat update failed.",
                    exc_info=True,
                    extra={
                        "job_id": self._job_id,
                        "progress_percent": next_progress,
                    },
                )

    def _write_progress(
        self,
        *,
        progress_percent: int,
    ) -> None:
        """Write one monotonic job progress update."""

        with psycopg.connect(
            settings.database_url,
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE jobs
                    SET progress_percent = GREATEST(
                            progress_percent,
                            %s
                        ),
                        updated_at = NOW()
                    WHERE job_id = %s
                      AND status = 'PROCESSING'
                    """,
                    (
                        progress_percent,
                        self._job_id,
                    ),
                )

            connection.commit()
