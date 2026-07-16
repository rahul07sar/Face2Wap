"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        face_swap_engine_factory.py
Module:      Worker / Face-Swap Engine
Description:

Creates and returns the configured Face2Wap face-swap engine.

The processing pipeline depends only on the FaceSwapEngine interface. This
factory selects the configured implementation without exposing engine-specific
details to the rest of the worker.

============================================================================
"""

from app.config import settings
from app.face_swap_engine_base import (
    FaceSwapEngine,
    FaceSwapEngineError,
)
from app.socaity_face_swap_engine import (
    socaity_face_swap_engine,
)


def get_face_swap_engine() -> FaceSwapEngine:
    """Return the configured face-swap engine."""

    if settings.face_swap_engine == "socaity":
        return socaity_face_swap_engine

    if settings.face_swap_engine == "facefusion":
        try:
            from app.facefusion_face_swap_engine import (
                facefusion_face_swap_engine,
            )

            return facefusion_face_swap_engine

        except ImportError as error:
            raise FaceSwapEngineError(
                "The configured FaceFusion engine is not installed.",
            ) from error

    raise FaceSwapEngineError(
        f"Unsupported face-swap engine: "
        f"{settings.face_swap_engine}",
    )
