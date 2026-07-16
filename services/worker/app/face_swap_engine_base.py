"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        face_swap_engine_base.py
Module:      Worker / Face-Swap Engine
Description:

Defines the common contract implemented by Face2Wap image face-swap engines.

The processing pipeline depends on this interface rather than a specific
third-party engine, allowing SocAIty, FaceFusion, and future engines to be
selected without changing job, storage, result, or API workflows.

============================================================================
"""

from abc import ABC, abstractmethod
from pathlib import Path


# ============================================================================
# Exceptions
# ============================================================================

class FaceSwapEngineError(RuntimeError):
    """Raised when a configured face-swap engine cannot complete a request."""


# ============================================================================
# Engine Contract
# ============================================================================

class FaceSwapEngine(ABC):
    """Common interface for Face2Wap image face-swap engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable configuration name of the engine."""

    @abstractmethod
    def swap_image(
        self,
        *,
        source_path: Path,
        target_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Swap the source identity onto the target image.

        Implementations must write the generated image to ``output_path`` and
        return that same path after confirming that a non-empty file exists.
        """