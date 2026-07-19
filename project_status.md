# Face2Wap — Project Status

Legend

- ✅ Done
- 🚧 In Progress
- ⏳ Todo

---

## Project Goal

Face2Wap is an open, production-grade face swap platform supporting both image and video face swapping through a pluggable face-swap engine architecture. The currently supported engines are FaceFusion (default) and SocAIty/face2face (legacy/fallback). The platform is designed to run locally during development while remaining cloud-ready for Google Cloud Platform deployment without architectural changes.

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

AI Engines
- FaceFusion (Default)
- SocAIty/face2face (Legacy/Fallback)

Engine Architecture
- Strategy Pattern
- Factory Pattern
- Pluggable FaceSwapEngine Interface

Video Processing
- FFmpeg

Database
- PostgreSQL (hosted in supabase)

Worker
- Python GPU Worker
- Local CPU-compatible worker mode for development

GPU (production hosted at)
- https://www.databasemart.com/
- Worker is hosted here only web + API in local (check)
- login: ssh administrator@204.12.253.252 , enter password, for sudo: sudo -i, enter password

Storage
- Local Storage (Development)

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
Face-Swap Engine Factory
      │
 ┌────┴────┐
 ▼         ▼
FaceFusion SocAIty/face2face
(Default)   (Fallback)
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



## Face-Swap Engine Architecture

Face2Wap uses a pluggable engine architecture.

Current Engines

- FaceFusion (Default)
- SocAIty/face2face (Legacy/Fallback)

The worker depends only on the `FaceSwapEngine` interface. New engines can be added by implementing the interface and registering them in the engine factory.

## Repository Structure

```txt
face2wap/

apps/
    web/

services/
    api/
    worker/
        app/
            face_swap_engine_base.py
            face_swap_engine_factory.py
            facefusion_face_swap_engine.py
            socaity_face_swap_engine.py

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
- FaceSwapEngine abstraction
- Face-swap engine factory
- Strategy-based engine selection
- Configuration-driven engine selection
- SocAIty/face2face engine adapter
- FaceFusion engine adapter
- FaceFusion headless CLI integration
- Engine-independent processing pipeline
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

## Remote GPU Notes 🚧

Current working direction

- Local web runs on the developer machine.
- Remote API runs on the GPU server.
- Remote worker runs on the GPU server.
- PostgreSQL is hosted on Supabase.
- GPU host provider is Database Mart.
- Storage is currently remote local-disk storage on the GPU box.

Current remote host

- Provider: Database Mart
- OS: Ubuntu Server 20 LTS 64-bit
- GPU verified: NVIDIA RTX A4000

Fresh GPU server setup

- Use Ubuntu 22.04 LTS or 24.04 LTS for a fresh rebuild if possible.
- Install host packages: `git`, `curl`, `ca-certificates`, `gnupg`, `lsb-release`
- Install Docker Engine from the official Docker apt repository
- Install Docker plugins: Buildx and Compose
- Install NVIDIA Container Toolkit
- Configure Docker to use the NVIDIA runtime
- Verify GPU on the host with `nvidia-smi`
- Verify GPU inside Docker with `docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi`
- Add GitHub deploy key for the private Face2Wap repository
- Clone the repository and create the persistent storage root

Fresh GPU server bootstrap commands

```bash
apt-get update
apt-get install -y ca-certificates curl gnupg git lsb-release

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

cat >/etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi
```

Fresh repository + storage bootstrap

```bash
mkdir -p /root/.ssh
# Add the GitHub deploy key first, then:
git clone <PRIVATE_REPO_URL> /root/face2wap

mkdir -p /root/face2wap-storage/uploads
mkdir -p /root/face2wap-storage/results
mkdir -p /root/face2wap-storage/temp

docker volume create face2wap_facefusion_assets
```

Fresh env files to create on the server

- `/root/face2wap/.env.api-remote`
- `/root/face2wap/.env.worker-smoke`

Minimum API env keys

- `DATABASE_URL=...`
- `JOB_TOKEN_SECRET=...`
- `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001`
- `WORKER_BASE_URL=http://127.0.0.1:8001`
- `WORKER_API_TOKEN=...`
- `WORKER_REQUEST_TIMEOUT_SECONDS=11100`

Minimum worker env keys

- `DATABASE_URL=postgresql://postgres.gjhtknqwgskppyqjwfap:[password-with-#-encoded-as-%23]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres`
- `WORKER_API_TOKEN=dev-worker-token`
- `FACE_SWAP_ENGINE=facefusion`
- `FACEFUSION_EXECUTION_PROVIDER=cuda`
- `FACEFUSION_EXECUTION_THREAD_COUNT=4`
- `FACEFUSION_VIDEO_MEMORY_STRATEGY=tolerant`
- `FACEFUSION_VIDEO_FACE_SWAPPER_MODEL=inswapper_128`
- `FACEFUSION_VIDEO_FACE_SWAPPER_PIXEL_BOOST=256x256`
- `FACEFUSION_OUTPUT_VIDEO_QUALITY=60`
- `FACEFUSION_OUTPUT_VIDEO_SCALE=0.5`
- `FACEFUSION_PROCESS_TIMEOUT_SECONDS=3600`
- `FACEFUSION_VIDEO_PROCESS_TIMEOUT_SECONDS=10800`
- `API_TRANSFER_TIMEOUT_SECONDS=11100`
- `API_BASE_URL=http://204.12.253.252:8000`

Remote repository path

- `/root/face2wap`

Remote worker image build

```bash
cd /root/face2wap
docker build -t face2wap-worker-gpu \
  --build-arg FACE2WAP_RUNTIME_VARIANT=gpu \
  --build-arg FACE2WAP_INSTALL_FACEFUSION=1 \
  --build-arg FACE2WAP_INSTALL_SOCAITY=0 \
  --build-arg FACEFUSION_REF=3.7.1 \
  -f services/worker/Dockerfile .
```

Remote worker runtime notes

- Worker health port: `8001`
- Worker env file: `/root/face2wap/.env.worker-smoke`
- Worker storage mount: `/root/face2wap-storage:/app/storage`
- FaceFusion model cache volume: `face2wap_facefusion_assets:/opt/facefusion/.assets`
- Current tuning being tested:
- `FACEFUSION_EXECUTION_THREAD_COUNT=4`
- `FACEFUSION_VIDEO_MEMORY_STRATEGY=tolerant`
- Timeout tuning now required for long jobs:
- `FACEFUSION_PROCESS_TIMEOUT_SECONDS=3600`
- `FACEFUSION_VIDEO_PROCESS_TIMEOUT_SECONDS=10800`
- `API_TRANSFER_TIMEOUT_SECONDS=11100`

Remote worker run

```bash
docker rm -f face2wap-worker-gpu 2>/dev/null || true
docker run -d \
  --name face2wap-worker-gpu \
  --gpus all \
  --env-file /root/face2wap/.env.worker-smoke \
  -p 8001:8001 \
  -v /root/face2wap-storage:/app/storage \
  -v face2wap_facefusion_assets:/opt/facefusion/.assets \
  face2wap-worker-gpu
```

Remote worker checks

```bash
curl http://127.0.0.1:8001/health
docker logs face2wap-worker-gpu --tail 100
docker logs -f face2wap-worker-gpu
docker stats face2wap-worker-gpu
```

Remote API image build

```bash
cd /root/face2wap
docker build -t face2wap-api-remote -f services/api/Dockerfile .
```

Remote API runtime notes

- API health port: `8000`
- API env file: `/root/face2wap/.env.api-remote`
- API storage mount: `/root/face2wap-storage:/app/storage`
- Required secret: `JOB_TOKEN_SECRET`
- `DATABASE_URL` must use the working Supabase Session Pooler URL
- If the DB password contains `#`, it must be URL-encoded as `%23`
- Long-running worker dispatches need:
- `WORKER_REQUEST_TIMEOUT_SECONDS=11100`

Remote API run

```bash
docker rm -f face2wap-api-remote 2>/dev/null || true
docker run -d \
  --name face2wap-api-remote \
  --network host \
  --env-file /root/face2wap/.env.api-remote \
  -v /root/face2wap-storage:/app/storage \
  face2wap-api-remote
```

Remote API checks

```bash
curl http://127.0.0.1:8000/health
docker logs face2wap-api-remote --tail 100
docker logs -f face2wap-api-remote
```

Local web note

- Local web can point to the remote API using:
- `NEXT_PUBLIC_API_BASE_URL=http://204.12.253.252:8000`
- If port `3000` is busy, Next.js may automatically start on `3001`

Remote storage layout on the GPU host

- Uploads: `/root/face2wap-storage/uploads`
- Results: `/root/face2wap-storage/results`
- Temp work files: `/root/face2wap-storage/temp`
- Uploaded assets are stored under:
- `/root/face2wap-storage/uploads/<job_id>/<asset_type>/<filename>`
- Result assets are stored under:
- `/root/face2wap-storage/results/<job_id>/<filename>`

Current remote notes

- Remote API and remote worker now exchange files through protected internal API endpoints.
- The worker no longer depends on sharing the API container's upload path directly.
- Long FaceFusion runs can keep the job busy for several minutes.
- Worker-side processing progress now heartbeats forward during the long FaceFusion step instead of freezing at the initial `20%` or `30%` milestone.
- If processing fails late around `70%` to `98%`, check timeout settings first:
- worker FaceFusion timeout
- worker result-upload timeout
- API worker-request timeout

Status

🚧 In Progress | Remote GPU API/worker are up, bootstrap steps are documented, and processing progress has been improved; final production hardening is still pending

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
- FaceFusion end-to-end verification
- Engine factory verification
- Engine selection verification

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
- Image Face Swap (FaceFusion + SocAIty)
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
