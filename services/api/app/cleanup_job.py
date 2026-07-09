"""
============================================================================
Face2Wap
----------------------------------------------------------------------------
File:        cleanup_job.py
Module:      API / Cleanup Job
Description:

Runs the Face2Wap cleanup pipeline as a standalone process. This is intended
for Docker cron, Cloud Run jobs, or future scheduled infrastructure.

============================================================================
"""

from app.cleanup_runner import run_cleanup
from app.database import get_connection


def main() -> None:
    """Run all cleanup tasks once."""

    connection_generator = get_connection()
    connection = next(connection_generator)

    try:
        result = run_cleanup(connection)
        print(result)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
    