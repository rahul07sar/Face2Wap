"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        api_transfer_client.py
Module:      Worker / API Transfer
Description:

Downloads validated worker input assets from the API and uploads generated
result files back to the API so processing can run on a remote worker host.

============================================================================
"""

from pathlib import Path
from typing import Any

import httpx

from app.config import settings


CHUNK_SIZE_BYTES = 64 * 1024


class WorkerApiTransferError(RuntimeError):
    """Raised when the worker cannot transfer files with the API."""


def _require_api_base_url() -> str:
    """Return the configured API base URL for worker transfers."""

    api_base_url = settings.api_base_url.strip().rstrip("/")

    if not api_base_url:
        raise WorkerApiTransferError(
            "API_BASE_URL is not configured.",
        )

    return api_base_url


def _create_timeout() -> httpx.Timeout:
    """Return the timeout used for worker-to-API file transfers."""

    return httpx.Timeout(
        settings.api_transfer_timeout_seconds,
        connect=10.0,
    )


def _worker_headers() -> dict[str, str]:
    """Return the authenticated headers used for internal API transfers."""

    worker_api_token = settings.worker_api_token.strip()

    if not worker_api_token:
        raise WorkerApiTransferError(
            "WORKER_API_TOKEN is not configured.",
        )

    return {
        "X-Worker-Token": worker_api_token,
        "Accept": "application/json",
    }


def _resolve_under_root(
    root: str,
    object_path: str,
) -> Path:
    """Resolve an object path safely under a configured local root."""

    storage_root = Path(root).resolve()
    target_path = (storage_root / object_path).resolve()

    if (
        storage_root not in target_path.parents
        and target_path != storage_root
    ):
        raise WorkerApiTransferError(
            "Resolved worker transfer path escaped its configured storage root.",
        )

    return target_path


def _prepare_download_path(
    *,
    job_id: str,
    asset_id: int,
    filename: str,
) -> Path:
    """Prepare a safe temporary file path for one downloaded worker asset."""

    normalized_job_id = job_id.strip()
    safe_filename = Path(filename).name or f"asset-{asset_id}.bin"
    object_path = (
        f"{normalized_job_id}/inputs/"
        f"{asset_id}-{safe_filename}"
    )

    download_path = _resolve_under_root(
        settings.local_temp_dir,
        object_path,
    )
    download_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return download_path


def download_worker_asset(
    *,
    job_id: str,
    asset_id: int,
    filename: str,
) -> Path:
    """Download one validated input asset from the API into worker temp storage."""

    api_base_url = _require_api_base_url()
    target_path = _prepare_download_path(
        job_id=job_id,
        asset_id=asset_id,
        filename=filename,
    )

    try:
        with httpx.Client(
            timeout=_create_timeout(),
        ) as client:
            with client.stream(
                "GET",
                (
                    f"{api_base_url}"
                    f"/internal/jobs/{job_id}/assets/{asset_id}/file"
                ),
                headers=_worker_headers(),
            ) as response:
                if not response.is_success:
                    raise WorkerApiTransferError(
                        _read_api_error(
                            response,
                            fallback_message=(
                                "The API rejected the worker asset download."
                            ),
                        ),
                    )

                with target_path.open("wb") as output:
                    for chunk in response.iter_bytes(
                        CHUNK_SIZE_BYTES,
                    ):
                        if chunk:
                            output.write(chunk)

    except httpx.TimeoutException as error:
        target_path.unlink(
            missing_ok=True,
        )
        raise WorkerApiTransferError(
            "Downloading the worker asset from the API timed out.",
        ) from error

    except httpx.HTTPError as error:
        target_path.unlink(
            missing_ok=True,
        )
        raise WorkerApiTransferError(
            "The worker could not download the asset from the API.",
        ) from error

    if (
        not target_path.is_file()
        or target_path.stat().st_size <= 0
    ):
        target_path.unlink(
            missing_ok=True,
        )
        raise WorkerApiTransferError(
            "The downloaded worker asset is empty.",
        )

    return target_path


def upload_worker_result(
    *,
    job_id: str,
    result_path: Path,
    filename: str,
    mime_type: str,
) -> dict:
    """Upload one generated result file back to the API."""

    if not result_path.is_file():
        raise WorkerApiTransferError(
            "The generated worker result file was not found.",
        )

    api_base_url = _require_api_base_url()

    try:
        with httpx.Client(
            timeout=_create_timeout(),
        ) as client:
            with result_path.open("rb") as result_file:
                response = client.post(
                    f"{api_base_url}/internal/jobs/{job_id}/result",
                    headers=_worker_headers(),
                    files={
                        "file": (
                            Path(filename).name or result_path.name,
                            result_file,
                            mime_type,
                        ),
                    },
                )

    except httpx.TimeoutException as error:
        completed_result = _read_completed_job_result(
            job_id=job_id,
        )

        if completed_result is not None:
            return completed_result

        raise WorkerApiTransferError(
            "Uploading the generated result back to the API timed out.",
        ) from error

    except httpx.HTTPError as error:
        completed_result = _read_completed_job_result(
            job_id=job_id,
        )

        if completed_result is not None:
            return completed_result

        raise WorkerApiTransferError(
            "The worker could not upload the generated result to the API.",
        ) from error

    if not response.is_success:
        raise WorkerApiTransferError(
            _read_api_error(
                response,
                fallback_message=(
                    "The API rejected the generated worker result."
                ),
            ),
        )

    try:
        payload: Any = response.json()
    except ValueError as error:
        raise WorkerApiTransferError(
            "The API returned an invalid worker result response.",
        ) from error

    return {
        "jobId": payload.get("jobId", job_id),
        "status": payload.get("status", "COMPLETED"),
        "progressPercent": payload.get(
            "progressPercent",
            100,
        ),
        "assetId": payload.get("assetId"),
        "objectPath": payload.get("objectPath"),
        "storageProvider": payload.get("storageProvider"),
        "sizeBytes": payload.get("sizeBytes"),
    }


def _read_completed_job_result(
    *,
    job_id: str,
) -> dict | None:
    """Return a completed result payload if the API already finalized the job."""

    api_base_url = _require_api_base_url()

    try:
        with httpx.Client(
            timeout=_create_timeout(),
        ) as client:
            response = client.get(
                f"{api_base_url}/jobs/{job_id}/status",
                headers={
                    "Accept": "application/json",
                },
            )
    except httpx.HTTPError:
        return None

    if not response.is_success:
        return None

    try:
        payload: Any = response.json()
    except ValueError:
        return None

    if payload.get("status") != "COMPLETED":
        return None

    return {
        "jobId": payload.get("jobId", job_id),
        "status": "COMPLETED",
        "progressPercent": payload.get(
            "progressPercent",
            100,
        ),
        "assetId": None,
        "objectPath": None,
        "storageProvider": None,
        "sizeBytes": None,
    }


def _read_api_error(
    response: httpx.Response,
    *,
    fallback_message: str,
) -> str:
    """Extract a readable error message from a failed API response."""

    try:
        payload: Any = response.json()
    except ValueError:
        return fallback_message

    detail = payload.get("detail")

    if isinstance(detail, str) and detail.strip():
        return detail.strip()

    return fallback_message
