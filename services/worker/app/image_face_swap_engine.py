"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        image_face_swap_engine.py
Module:      Worker / Image Processing
Description:

Provides a production-facing adapter around the SocAIty/face2face image
face-swap engine.

The adapter validates source, target, and output paths, loads the model lazily,
runs image-to-image face swapping, and writes the generated image into the
worker temporary directory.

============================================================================
"""

from pathlib import Path
from threading import Lock
from typing import Any, Optional

import cv2

from app.config import settings


# ============================================================================
# Exceptions
# ============================================================================

class ImageFaceSwapError(RuntimeError):
    """Raised when an image face-swap operation cannot be completed."""


# ============================================================================
# Path Handling
# ============================================================================

def _resolve_under_root(
    root: str,
    object_path: str,
) -> Path:
    """Resolve an object path safely under a configured storage root."""

    storage_root = Path(root).resolve()
    resolved_path = (storage_root / object_path).resolve()

    if (
        storage_root not in resolved_path.parents
        and resolved_path != storage_root
    ):
        raise ImageFaceSwapError(
            "Resolved image path escaped its configured storage root.",
        )

    return resolved_path


def resolve_worker_upload_path(
    object_path: str,
) -> Path:
    """Resolve and validate an uploaded worker asset path."""

    upload_path = _resolve_under_root(
        settings.local_upload_dir,
        object_path,
    )

    if not upload_path.is_file():
        raise ImageFaceSwapError(
            f"Worker input asset does not exist: {object_path}",
        )

    return upload_path


def prepare_worker_temp_image_path(
    *,
    job_id: str,
    filename: str,
) -> Path:
    """Prepare a safe temporary output path for an image-swap job."""

    if not job_id.strip():
        raise ImageFaceSwapError(
            "A job ID is required to prepare the image result path.",
        )

    safe_filename = Path(filename).name

    if not safe_filename:
        raise ImageFaceSwapError(
            "A result filename is required.",
        )

    file_extension = Path(safe_filename).suffix.lower()

    if file_extension not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }:
        raise ImageFaceSwapError(
            "Image results must use JPG, JPEG, PNG, or WebP.",
        )

    object_path = f"{job_id}/{safe_filename}"

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
# Face-Swap Engine
# ============================================================================

class ImageFaceSwapEngine:
    """Lazy-loading adapter for SocAIty/face2face image inference."""

    def __init__(
        self,
        *,
        device_id: int = 0,
    ) -> None:
        self._device_id = device_id
        self._engine: Optional[Any] = None
        self._engine_lock = Lock()

    def _get_engine(self) -> Any:
        """Load and cache the face-swap model on first use."""

        if self._engine is not None:
            return self._engine

        with self._engine_lock:
            if self._engine is not None:
                return self._engine

            try:
                from face2face import Face2Face
            except ImportError as error:
                raise ImageFaceSwapError(
                    "Face-swap functionality is temporarily not available.",
                ) from error

            try:
                self._engine = Face2Face(
                    device_id=self._device_id,
                )
            except Exception as error:
                raise ImageFaceSwapError(
                    "Face swap processing could not be initialized, try again later.",
                ) from error

        return self._engine

    def swap_image(
        self,
        *,
        source_path: Path,
        target_path: Path,
        output_path: Path,
    ) -> Path:
        """Swap the source face onto the target image and save the result."""

        if not source_path.is_file():
            raise ImageFaceSwapError(
                "Source face image was not found.",
            )

        if not target_path.is_file():
            raise ImageFaceSwapError(
                "Target image was not found.",
            )

        if source_path.resolve() == target_path.resolve():
            raise ImageFaceSwapError(
                "Source and target images must be different files.",
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        engine = self._get_engine()

        try:
            generated_image = engine.swap_img_to_img(
                str(source_path),
                str(target_path),
                enhance_face_model=None,
            )
        except Exception:
            raise ImageFaceSwapError(
                "The face-swap failed to process the images.",
            )

        # Restore/enhance the swapped face.
        try:
            generated_image = engine.enhance_faces(
                generated_image,
                model="gfpgan_1.4",
            )

        except Exception as error:
            raise ImageFaceSwapError(
                "The face-swap engine failed to process the images.",
            ) from error

        if generated_image is None:
            raise ImageFaceSwapError(
                "The face-swap engine returned no image.",
            )

        try:
            image_written = cv2.imwrite(
                str(output_path),
                generated_image,
            )
        except Exception as error:
            output_path.unlink(
                missing_ok=True,
            )

            raise ImageFaceSwapError(
                "The generated face-swap image could not be written.",
            ) from error

        if not image_written or not output_path.is_file():
            output_path.unlink(
                missing_ok=True,
            )

            raise ImageFaceSwapError(
                "The generated face-swap image was not saved.",
            )

        if output_path.stat().st_size <= 0:
            output_path.unlink(
                missing_ok=True,
            )

            raise ImageFaceSwapError(
                "The generated face-swap image is empty.",
            )

        return output_path


image_face_swap_engine = ImageFaceSwapEngine()
