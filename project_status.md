# Face2Wap — Project Status

1.[Done]
2. [Todo]
3. [In progress]

## Project Goal

Face2Wap is an open, production-grade face swap tool using a Next.js UI, GCP hosting, Cloud Storage, queued GPU processing, and the `SocAIty/face2face` engine for both image and video face swap.

## Product Type

Open product, no user login for v1.

Access is based on anonymous job tracking:

* `jobId`: public job identifier
* `jobToken`: private access token for viewing result

## Core Stack

* Frontend: Next.js
* Backend API: FastAPI or Next.js API
* Face Swap Engine: `SocAIty/face2face`
* Video Processing: FFmpeg
* Cloud: Google Cloud Platform
* Storage: Google Cloud Storage
* Queue: Cloud Tasks or Pub/Sub
* Database: PostgreSQL
* Worker: Python GPU worker
* Deployment: Cloud Run, Compute Engine GPU, or GKE GPU

## High-Level Architecture

```txt
Next.js UI
  ↓
API Service
  ↓
PostgreSQL Job Database
  ↓
Cloud Storage Signed Upload URLs
  ↓
Cloud Tasks / Pub/Sub Queue
  ↓
Python GPU Worker
  ↓
Face2Face + FFmpeg
  ↓
Cloud Storage Result
  ↓
Job Status / Result Page
```

## Suggested Repository Structure

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
    project_status.md
```

## Database Tables

```txt
jobs
job_assets
job_events
moderation_flags
rate_limits
audit_logs
system_settings
```

## Job Status Values

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

## Phase 1 — Foundation [Done]

Tasks:

* Create monorepo structure
* Create Next.js frontend app
* Create API service
* Create Python worker service
* Add Dockerfiles
* Add `.env`
* Add project documentation
* Add GCP bucket plan
* Add PostgreSQL schema plan
* Add basic health check APIs

Status: Completed

## Phase 2 — Open Job System

Tasks:
* Create anonymous job API [Done]
* Generate `jobId` [Done]
* Generate private `jobToken` [Done]
* Store job in PostgreSQL [Done]
* Add job expiry time [Done]
* Add job status API [Done]
* Add job result API [Done]
* Add audit log entry for each job action [Done]
* Add basic IP-based rate limit [Done]

Status: Completed

## Phase 3 — Upload System

Tasks:

* Add source face image upload
* Add target image upload
* Add target video upload
* Generate signed upload URLs
* Validate file type
* Validate file size
* Store asset metadata
* Block unsupported files
* Add upload expiry
* Add automatic cleanup plan

Status: In progress

## Phase 4 — Image Face Swap

Tasks:

* Connect worker with queued image jobs
* Download source and target image from GCS
* Run face detection
* Run face swap using `face2face`
* Save output image to GCS
* Update job status
* Save worker logs
* Add failure handling
* Add result preview page

Status: Pending

## Phase 5 — Video Face Swap

Tasks:

* Accept target video upload
* Validate video duration
* Validate video size
* Extract frames using FFmpeg
* Detect faces frame-by-frame
* Run face swap on video frames
* Preserve original audio
* Rebuild video using FFmpeg
* Save output video to GCS
* Track video job progress
* Add progress percentage
* Add timeout handling
* Add retry handling
* Add failed-frame recovery logic
* Add result download page

Status: Pending

## Phase 6 — Queue and Worker Reliability

Tasks:

* Add Cloud Tasks or Pub/Sub
* Add retry limits
* Add dead-letter handling
* Add worker heartbeat
* Add job timeout
* Add GPU warmup logic
* Add worker concurrency control
* Add memory and disk cleanup
* Add structured logs
* Add failed job diagnostics

Status: Pending

## Phase 7 — Safety and Abuse Protection

Tasks:

* Add consent checkbox
* Add watermark option
* Add NSFW input detection
* Add blocked content rules
* Add public-figure/celebrity policy layer if required
* Add abuse reporting
* Add rate limit by IP
* Add temporary file deletion
* Add audit logs
* Add admin-only review mode later

Status: Pending

## Phase 8 — Production Deployment

Tasks:

* Deploy Next.js UI
* Deploy API service
* Deploy PostgreSQL
* Create GCS buckets
* Configure signed URLs
* Deploy GPU worker
* Configure queue
* Configure secrets
* Add HTTPS
* Add domain
* Add logging
* Add monitoring
* Add alerting
* Add backup policy

Status: Pending

## Phase 9 — UI Pages

Tasks:

* Home page
* Upload page
* Job progress page
* Result page
* Error page
* Privacy page
* Terms page
* Safety notice page

Status: Pending

## Phase 10 — Testing

Tasks:

* API unit tests
* Worker unit tests
* Image swap test
* Video swap test
* Upload validation test
* Queue retry test
* Expired job test
* Failed job test
* Rate limit test
* GCS signed URL test
* End-to-end job test

Status: Pending

## Phase 11 — Cost and Scaling

Tasks:

* Limit max image size
* Limit max video duration
* Limit concurrent jobs
* Add queue backpressure
* Add GPU autoscaling plan
* Add cleanup cron
* Add storage lifecycle rule
* Add cost monitoring
* Add usage dashboard

Status: Pending

## MVP Scope

The MVP must include:

* Open access without login
* Anonymous job token
* Image face swap
* Video face swap
* GCS upload/result storage
* Queue-based processing
* PostgreSQL job tracking
* GPU worker
* Basic abuse protection
* Auto-delete old files

## Not Included in v1

* User login
* User dashboard
* Payments
* Credits
* Team accounts
* Admin panel
* Mobile app

## Current Status

Project is in planning phase.

Next recommended file:

```txt
docs/architecture.md
```

After that:

```txt
database/schema.sql
services/api
services/worker
apps/web
```
