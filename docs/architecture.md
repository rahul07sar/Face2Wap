# ============================================================================
# Face2Wap
# ----------------------------------------------------------------------------
# Architecture Documentation
# ============================================================================

# Face2Wap Architecture

Face2Wap is an open face swap product using a Next.js UI, API service, PostgreSQL, Cloud Storage, queue-based processing, and a Python GPU worker.

## Services

```txt
apps/web          Next.js frontend
services/api      Public API and job orchestration
services/worker   GPU worker using SocAIty/face2face and FFmpeg
database          PostgreSQL migrations and schema
infra             Docker and GCP deployment files
docs              Project documentation