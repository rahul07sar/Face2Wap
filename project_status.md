# Face2Wap — Project Status

Legend

- ✅ Done
- 🚧 In Progress
- ⏳ Todo

---

## Project Goal

Face2Wap is an open, production-grade face swap platform supporting both image and video face swapping using the SocAIty/face2face engine. The platform is designed to run locally during development while remaining cloud-ready for Google Cloud Platform deployment without architectural changes.

---

## Product Type

Open product (v1)

No authentication required.

Anonymous jobs are identified using:

- jobId (public identifier)
- jobToken (private access token)

---

## Core Stack

Frontend
- Next.js
- TypeScript

Backend
- FastAPI

AI Engine
- SocAIty/face2face

Video Processing
- FFmpeg

Database
- PostgreSQL

Worker
- Python GPU Worker

Storage
- Local Storage (Development)
- Google Cloud Storage (Production)

Queue
- Cloud Tasks / PubSub (Production)

Deployment
- Docker
- Cloud Run
- Compute Engine GPU
- GKE GPU

---

## High-Level Architecture

```txt
Next.js UI
      │
      ▼
FastAPI API
      │
      ▼
PostgreSQL
      │
      ▼
Storage Provider
(Local / GCS)
      │
      ▼
Queue
      │
      ▼
Python Worker
      │
      ▼
SocAIty/face2face
      │
      ▼
Result Storage
      │
      ▼
Result API
```

## Storage Strategy

Face2Wap uses a provider abstraction so the upload pipeline is identical in development and production.

```txt
Development
───────────
API
 ↓
Local Storage

Production
──────────
API
 ↓
Google Cloud Storage
```

The worker consumes assets through the storage provider abstraction, allowing local development and GCP deployment to share the same processing pipeline with minimal configuration changes.

---

## Repository Structure

```txt
face2wap/

apps/
    web/

services/
    api/
    worker/

database/
    migrations/

infra/
    docker/
    gcp/

docs/

storage/
    uploads/
    results/
    temp/
```

---

## Database Tables

Current

```txt
jobs
job_assets
job_events
audit_logs
rate_limits
```

Planned

```txt
moderation_flags
system_settings
```

---

## Job Status

```txt
PENDING
UPLOADING
QUEUED
PROCESSING
COMPLETED
FAILED
EXPIRED
BLOCKED
```

---

# Phase 1 — Foundation ✅

Completed

- Monorepo
- Next.js
- FastAPI
- Worker
- Docker
- Docker Compose
- PostgreSQL
- Database migrations
- Local .env
- Project documentation
- GCP planning
- Health APIs

Status

✅ Completed

---

# Phase 2 — Open Job System ✅

Completed

- Anonymous Job API
- jobId generation
- jobToken generation
- PostgreSQL persistence
- Expiry handling
- Status API
- Result API
- Audit logging
- IP Rate Limiting

Status

✅ Completed

---

# Phase 3 — Upload System 🚧

## Phase 3.1 — Upload Preparation ✅

Completed

- Upload preparation API
- Local/GCS storage abstraction
- Upload metadata
- Asset metadata persistence
- Upload expiry
- File type validation
- File size validation
- Unsupported file blocking
- Upload slot generation
- Asset-specific upload URL generation
- Audit logging

Status

✅ Completed

---

## Phase 3.2 — Upload Pipeline 🚧

Completed

- Production multipart upload API
- Streaming upload (constant memory)
- Source face image upload
- SHA-256 checksum generation
- Upload status transitions
- Validation status transitions
- Uploaded file size persistence
- Local storage persistence
- Upload audit logging
- Upload ownership validation
- Upload expiry validation
- MIME type validation
- Asset upload endpoint
- Job/Asset verification

In Progress

- Target image upload validation
- Target video upload validation
- Image metadata extraction (width/height)
- Video metadata extraction (duration/resolution)
- Upload progress tracking
- Upload completion endpoint
- Upload retry support

Status

🚧 In Progress

---

## Phase 3.3 — Storage Providers 🚧

Completed

Local Provider

- Storage abstraction
- Upload path generation
- Local filesystem support

In Progress

Local Provider

- Read file
- Delete file
- Result storage

Google Cloud Storage

- Signed upload URLs
- Signed download URLs
- Provider implementation
- Automatic provider switching

Status

🚧 In Progress

---

## Phase 3.4 — Cleanup ⏳

Todo

- Upload expiry cleanup
- Result expiry cleanup
- Orphan cleanup
- Temp cleanup
- Scheduled cleanup worker

Status

⏳ Todo

---

## Phase 3.5 — Upload UI ⏳

Todo

- Light Mode
- Dark Mode
- Theme persistence
- Drag & Drop
- File picker
- Image preview
- Video preview
- Upload progress
- Cancel upload
- Retry upload
- Mobile responsive
- Desktop responsive

Status

⏳ Todo

---

# Phase 4 — Image Face Swap ⏳

- Queue integration
- Worker integration
- Face detection
- Face swap
- Face restoration
- Save result
- Result preview
- Failure handling

Status

⏳ Todo

---

# Phase 5 — Video Face Swap ⏳

- Target video processing
- Frame extraction
- Frame face detection
- Frame swapping
- Face restoration
- Audio preservation
- Video rebuild
- Progress tracking
- Retry support
- Timeout handling
- Failed frame recovery

Status

⏳ Todo

---

# Phase 6 — Queue & Worker Reliability ⏳

- Cloud Tasks
- Pub/Sub
- Retry policy
- Dead Letter Queue
- Worker heartbeat
- GPU warmup
- Worker concurrency
- Structured logging
- Diagnostics

Status

⏳ Todo

---

# Phase 7 — Safety & Moderation ⏳

- Consent
- Watermark
- NSFW detection
- Abuse detection
- Public figure policy
- Audit logging
- Cleanup
- Admin review

Status

⏳ Todo

---

# Phase 8 — Production Deployment ⏳

- Cloud Run
- Compute Engine GPU
- GCS
- Secrets
- HTTPS
- Monitoring
- Logging
- Alerts
- Backup

Status

⏳ Todo

---

# Phase 9 — Frontend ⏳

- Home
- Upload
- Job Progress
- Results
- Error
- Privacy
- Terms
- Safety

Status

⏳ Todo

---

# Phase 10 — Testing ⏳

- API Tests
- Upload Tests
- Worker Tests
- Queue Tests
- Image Tests
- Video Tests
- End-to-End Tests

Status

⏳ Todo

---

# Phase 11 — Scaling & Cost ⏳

- Upload limits
- Video limits
- Concurrency
- Storage lifecycle
- Autoscaling
- Cost monitoring
- Usage dashboard

Status

⏳ Todo

---

## MVP

- Anonymous jobs
- Image Face Swap
- Video Face Swap
- Local Storage
- GCS Support
- Queue
- PostgreSQL
- GPU Worker
- Basic Safety
- Automatic Cleanup

---

## Not Included (v1)

- Authentication
- Payments
- Credits
- Admin Portal
- Team Accounts
- Mobile Applications

---
