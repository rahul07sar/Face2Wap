/*
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        001_init.sql
 * Module:      Database / Migrations
 * Description:
 *
 * Creates the initial PostgreSQL schema required for Face2Wap job,
 * asset, and event tracking.
 *
 * ============================================================================
 */

BEGIN;

/* ============================================================================
 * Jobs
 * ============================================================================
 */

CREATE TABLE IF NOT EXISTS jobs (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL UNIQUE,
    job_token_hash VARCHAR(255) NOT NULL,
    job_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    progress_percent INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_jobs_progress_percent
        CHECK (progress_percent >= 0 AND progress_percent <= 100)
);

/* ============================================================================
 * Job Assets
 * ============================================================================
 */

CREATE TABLE IF NOT EXISTS job_assets (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL,
    asset_type VARCHAR(64) NOT NULL,
    bucket_name VARCHAR(255) NOT NULL,
    object_path TEXT NOT NULL,
    mime_type VARCHAR(128),
    size_bytes BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_job_assets_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_job_assets_size_bytes
        CHECK (size_bytes IS NULL OR size_bytes >= 0)
);

/* ============================================================================
 * Job Events
 * ============================================================================
 */

CREATE TABLE IF NOT EXISTS job_events (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_job_events_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE
);

/* ============================================================================
 * Indexes
 * ============================================================================
 */

CREATE INDEX IF NOT EXISTS idx_jobs_status
    ON jobs(status);

CREATE INDEX IF NOT EXISTS idx_jobs_expires_at
    ON jobs(expires_at);

CREATE INDEX IF NOT EXISTS idx_job_assets_job_id
    ON job_assets(job_id);

CREATE INDEX IF NOT EXISTS idx_job_events_job_id
    ON job_events(job_id);

COMMIT;
