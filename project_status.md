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
- Local CPU-compatible worker mode for development

Storage
- Local Storage (Development)
- Google Cloud Storage (Production)

Queue
- Internal API-to-worker dispatch (Development)
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
Queue / Worker Dispatch
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

## Phase 3.2 — Upload Pipeline ✅

Completed

- Production multipart upload API
- Streaming upload (constant memory)
- Source face image upload
- Target image upload
- Target video upload
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
- Image metadata extraction using Pillow
- Image width extraction
- Image height extraction
- Video metadata extraction using FFprobe
- Video width extraction
- Video height extraction
- Video duration extraction
- FFmpeg/FFprobe support in API Docker container
- Source image upload tested successfully
- Target image upload tested successfully
- Target video upload tested successfully
- Image metadata persistence tested successfully
- Video metadata persistence tested successfully
- Metadata extraction failure handling
- Invalid image detection
- Invalid file rejection with HTTP 400
- Failed upload database state persistence
- Validation error persistence
- Invalid physical file cleanup
- Orphan file prevention after metadata validation failure
- Upload retry API
- Failed asset retry validation
- FAILED to PREPARED state transition
- Validation state cleanup during retry
- Validation error cleanup during retry
- Upload metadata cleanup during retry
- Fresh upload expiry generation during retry
- Defensive physical file cleanup during retry
- Same asset ID preservation during retry
- Upload retry lifecycle tested successfully
- Upload progress tracking
- Upload completion endpoint

Status

✅ Completed

---

## Phase 3.3 — Storage Providers 🚧

✅ Done

Local Provider

- Storage abstraction
- Upload path generation
- Local filesystem support
- Local upload writes
- Invalid file deletion
- Failed upload defensive cleanup
- Local upload path resolver
- Local result path resolver
- Local file existence check
- Local file delete helper
- Local missing-file delete handling
- Local result path preparation
- Result asset registration helper
- Local result file copy helper
- Upload path traversal protection
- Result path traversal protection
- Local storage helper tests
- Result storage helper tests
- Storage provider interface extended
- Local provider read/delete/result methods
- GCS provider placeholder aligned to interface
- Worker configuration integration
- Worker PostgreSQL integration
- Worker result path preparation
- Worker result file copying
- Worker result source preservation
- Worker result path traversal protection
- Worker result storage tests
- Worker result database registration
- Worker job completion update
- Worker result registration integration test

🚧 In Progress

Google Cloud Storage

- Signed upload URLs
- Signed download URLs
- Provider implementation
- Automatic provider switching
- GCS upload progress compatibility

Status

🚧 In Progress | Local Provider completed; GCS provider remains

---

## Phase 3.4 — Cleanup ✅

Completed

- Upload expiry cleanup
- Result expiry cleanup
- Orphan/Unidentified cleanup
- Temp cleanup
- Scheduled cleanup worker

Status

✅ Completed

---

## Phase 3.5 — Upload UI 🚧

✅ Done

- Light Mode
- Dark Mode
- Theme persistence
- Drag & Drop
- File picker
- Source image preview
- Target image preview
- Target video preview
- Upload progress
- Upload success state
- Upload failure state
- Retry upload action
- Desktop responsive layout
- Mobile responsive layout
- Styled back-to-source action
- Start Face Swap button
- Processing status polling
- Live processing percentage
- Queued, processing, completed, and failed UI states

🚧 In Progress

- Cancel active upload
- Result preview
- Result download action
- Sanitized user-facing processing errors

Status

🚧 In Progress | Upload and processing UI working; result delivery remains

---

# Phase 4 — Image Face Swap 🚧

✅ Done

- Image processing API endpoint
- Anonymous job-token verification
- Queue readiness validation
- PENDING to QUEUED transition
- Protected API-to-worker dispatch
- Worker API token validation
- Worker image-job claiming
- PostgreSQL row locking
- QUEUED to PROCESSING transition
- Validated source asset resolution
- Validated target asset resolution
- Local upload path protection
- Worker temporary result path protection
- SocAIty/face2face engine adapter
- Lazy model initialization
- Local CPU-compatible development processing
- Image face-swap inference
- Processing progress updates
- Temporary result generation
- Result file storage
- Result asset registration
- Job completion update
- Temporary file cleanup
- Processing failure persistence
- Frontend Start Face Swap action
- Frontend status polling
- Frontend live progress display
- End-to-end image processing completed successfully

🚧 In Progress

- Result API delivery integration
- Result image preview in the frontend
- Result download action
- Safe centralized error sanitization
- Face restoration/enhancement
- Processing retry support
- Dedicated Phase 4 unit and integration tests

Status

🚧 In Progress | Core image face swap works end to end; result presentation and hardening remain

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

# Phase 6 — Queue & Worker Reliability 🚧

✅ Done for local development

- Protected internal API-to-worker dispatch
- Worker request timeout configuration
- Duplicate processing prevention
- Database-backed job claiming
- Worker progress persistence
- Worker failure persistence

⏳ Production queue work

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

🚧 In Progress | Local dispatch works; production queue reliability remains

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

# Phase 9 — Frontend 🚧

✅ Done

- Home
- Upload
- Upload previews
- Upload progress
- Job processing progress
- Processing success state
- Processing failure state
- Light/Dark theme

🚧 In Progress

- Results
- Result preview
- Result download
- Error hardening
- Privacy
- Terms
- Safety

Status

🚧 In Progress

---

# Phase 10 — Testing 🚧

✅ Existing coverage

- Upload tests
- Local storage tests
- Result storage tests
- Path-traversal tests
- Cleanup tests
- Worker result tests
- Worker/PostgreSQL integration tests
- Manual end-to-end image processing verification

🚧 Remaining

- Image engine adapter tests
- Image job-claim tests
- Image processing orchestration tests
- API queue/dispatch tests
- Frontend processing tests
- Video tests
- Full automated end-to-end tests

Status

🚧 In Progress

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
