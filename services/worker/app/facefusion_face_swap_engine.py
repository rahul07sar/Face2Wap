"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        facefusion_face_swap_engine.py
Module:      Worker / Face-Swap Engine
Description:

Provides the FaceFusion implementation of the Face2Wap face-swap engine.

This adapter executes FaceFusion in headless mode while exposing the common
FaceSwapEngine interface used by the worker processing pipeline.

============================================================================
"""

import logging
import subprocess
from pathlib import Path

from app.config import settings
from app.face_swap_engine_base import (
    FaceSwapEngine,
    FaceSwapEngineError,
)


logger = logging.getLogger(__name__)


class FaceFusionFaceSwapEngine(FaceSwapEngine):
    """FaceFusion image face-swap engine."""

    def _resolve_facefusion_program_path(self) -> Path:
        """Resolve the FaceFusion entrypoint inside the configured checkout."""

        working_directory = Path(
            settings.facefusion_working_directory,
        ).resolve()

        program_path = (
            working_directory
            / "facefusion.py"
        )

        if not working_directory.is_dir():
            raise FaceSwapEngineError(
                "Face-swap processing is temporarily unavailable.",
            )

        if not program_path.is_file():
            raise FaceSwapEngineError(
                "Face-swap processing is temporarily unavailable.",
            )

        return program_path

    def _validate_paths(
        self,
        *,
        source_path: Path,
        target_path: Path,
        output_path: Path,
    ) -> None:
        """Validate input and output paths before invoking FaceFusion."""

        if not source_path.is_file():
            raise FaceSwapEngineError(
                "Source face image was not found.",
            )

        if not target_path.is_file():
            raise FaceSwapEngineError(
                "Target media was not found.",
            )

        if (
            source_path.resolve()
            == target_path.resolve()
        ):
            raise FaceSwapEngineError(
                "Source and target images must be different files.",
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _collect_processors(self) -> list[str]:
        """Return the FaceFusion processors used for image swapping."""

        processors = [
            "face_swapper",
        ]

        if (
            settings.facefusion_enable_face_enhancer
        ):
            processors.append(
                "face_enhancer",
            )

        return processors

    def _collect_download_providers(
        self,
    ) -> list[str]:
        """Return configured download providers for FaceFusion assets."""

        providers = [
            provider.strip()
            for provider in (
                settings
                .facefusion_download_providers
                .split()
            )
            if provider.strip()
        ]

        return providers or [
            "github",
            "huggingface",
        ]

    def _build_headless_command(
        self,
        *,
        source_path: Path,
        target_path: Path,
        output_path: Path,
        program_path: Path,
    ) -> list[str]:
        """Build the FaceFusion headless command for one image-swap job."""

        command = [
            settings.facefusion_python_executable,
            str(program_path),
            "headless-run",
            "--source-paths",
            str(source_path),
            "--target-path",
            str(target_path),
            "--output-path",
            str(output_path),
            "--temp-path",
            str(output_path.parent),
            "--processors",
            *self._collect_processors(),
            "--face-swapper-model",
            settings.facefusion_face_swapper_model,
            "--face-swapper-pixel-boost",
            settings.facefusion_face_swapper_pixel_boost,
            "--execution-device-ids",
            str(settings.face_swap_device_id),
            "--execution-providers",
            settings.facefusion_execution_provider,
            "--execution-thread-count",
            str(
                settings
                .facefusion_execution_thread_count
            ),
            "--download-providers",
            *self._collect_download_providers(),
            "--output-image-quality",
            str(
                settings
                .facefusion_output_image_quality
            ),
            "--log-level",
            settings.facefusion_log_level,
        ]

        if (
            settings.facefusion_enable_face_enhancer
        ):
            command.extend(
                [
                    "--face-enhancer-model",
                    settings.facefusion_face_enhancer_model,
                    "--face-enhancer-blend",
                    str(
                        settings
                        .facefusion_face_enhancer_blend
                    ),
                    "--face-enhancer-weight",
                    str(
                        settings
                        .facefusion_face_enhancer_weight
                    ),
                ],
            )

        if settings.facefusion_keep_temp:
            command.append(
                "--keep-temp",
            )

        return command

    def _read_process_output(
        self,
        completed_process: subprocess.CompletedProcess[str],
    ) -> str:
        """Return the most useful FaceFusion process diagnostic."""

        output_parts = [
            completed_process.stderr.strip(),
            completed_process.stdout.strip(),
        ]

        for part in output_parts:
            if part:
                return (
                    part
                    .splitlines()[-1][:1000]
                )

        return (
            "FaceFusion exited without "
            "a diagnostic message."
        )

    def _execute_facefusion(
        self,
        *,
        command: list[str],
        program_path: Path,
        output_path: Path,
    ) -> Path:
        """Run FaceFusion, validate the result file, and return it."""

        try:
            completed_process = subprocess.run(
                command,
                cwd=str(program_path.parent),
                capture_output=True,
                text=True,
                check=False,
                timeout=(
                    settings
                    .facefusion_process_timeout_seconds
                ),
            )

        except subprocess.TimeoutExpired as error:
            output_path.unlink(
                missing_ok=True,
            )

            logger.exception(
                "FaceFusion image processing timed out.",
            )

            raise FaceSwapEngineError(
                "Face-swap processing timed out. Please try again.",
            ) from error

        except OSError as error:
            output_path.unlink(
                missing_ok=True,
            )

            logger.exception(
                "FaceFusion process could not be started.",
            )

            raise FaceSwapEngineError(
                "Face-swap processing is temporarily unavailable.",
            ) from error

        if completed_process.returncode != 0:
            output_path.unlink(
                missing_ok=True,
            )

            diagnostic = (
                self._read_process_output(
                    completed_process,
                )
            )

            logger.error(
                "FaceFusion image processing failed. "
                "Return code: %s. Diagnostic: %s",
                completed_process.returncode,
                diagnostic,
            )

            raise FaceSwapEngineError(
                "Face-swap processing could not be completed. "
                "Please try again.",
            )

        if not output_path.is_file():
            logger.error(
                "FaceFusion completed successfully but did not "
                "create an output file.",
            )

            raise FaceSwapEngineError(
                "The generated face-swap result is unavailable.",
            )

        if output_path.stat().st_size <= 0:
            output_path.unlink(
                missing_ok=True,
            )

            logger.error(
                "FaceFusion generated an empty output file.",
            )

            raise FaceSwapEngineError(
                "The generated face-swap result is unavailable.",
            )

        return output_path

    @property
    def name(self) -> str:
        """Return the stable engine name."""

        return "facefusion"

    def swap_image(
        self,
        *,
        source_path: Path,
        target_path: Path,
        output_path: Path,
    ) -> Path:
        """Execute a FaceFusion headless image face swap."""

        self._validate_paths(
            source_path=source_path,
            target_path=target_path,
            output_path=output_path,
        )

        program_path = (
            self
            ._resolve_facefusion_program_path()
        )

        command = self._build_headless_command(
            source_path=source_path,
            target_path=target_path,
            output_path=output_path,
            program_path=program_path,
        )

        # Prevent a stale result from being accepted if this execution fails.
        output_path.unlink(
            missing_ok=True,
        )

        logger.info(
            "Starting FaceFusion image processing.",
            extra={
                "engine": self.name,
                "source_path": str(source_path),
                "target_path": str(target_path),
                "output_path": str(output_path),
            },
        )

        output_path = self._execute_facefusion(
            command=command,
            program_path=program_path,
            output_path=output_path,
        )

        logger.info(
            "FaceFusion image processing completed successfully.",
            extra={
                "engine": self.name,
                "output_path": str(output_path),
                "output_size_bytes": (
                    output_path.stat().st_size
                ),
            },
        )

        return output_path

    def swap_video(
        self,
        *,
        source_path: Path,
        target_path: Path,
        output_path: Path,
    ) -> Path:
        """Execute a FaceFusion headless video face swap."""

        self._validate_paths(
            source_path=source_path,
            target_path=target_path,
            output_path=output_path,
        )

        program_path = (
            self
            ._resolve_facefusion_program_path()
        )

        command = self._build_headless_command(
            source_path=source_path,
            target_path=target_path,
            output_path=output_path,
            program_path=program_path,
        )

        output_path.unlink(
            missing_ok=True,
        )

        logger.info(
            "Starting FaceFusion video processing.",
            extra={
                "engine": self.name,
                "source_path": str(source_path),
                "target_path": str(target_path),
                "output_path": str(output_path),
            },
        )

        output_path = self._execute_facefusion(
            command=command,
            program_path=program_path,
            output_path=output_path,
        )

        logger.info(
            "FaceFusion video processing completed successfully.",
            extra={
                "engine": self.name,
                "output_path": str(output_path),
                "output_size_bytes": output_path.stat().st_size,
            },
        )

        return output_path


facefusion_face_swap_engine = (
    FaceFusionFaceSwapEngine()
)
