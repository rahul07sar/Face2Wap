/*
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        006_video_uploads.sql
 * Module:      Database / Migrations
 * Description:
 *
 * Adds a dedicated table for target video uploads so video-specific metadata
 * and future processing fields are stored separately from generic job assets.
 *
 * ============================================================================
 */

BEGIN;

CREATE TABLE IF NOT EXISTS job_video_uploads (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT NOT NULL UNIQUE,
    job_id VARCHAR(64) NOT NULL,
    object_path TEXT NOT NULL,
    mime_type VARCHAR(128),
    original_filename TEXT,
    size_bytes BIGINT,
    width INTEGER,
    height INTEGER,
    duration_seconds NUMERIC(12, 3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_job_video_uploads_asset
        FOREIGN KEY (asset_id)
        REFERENCES job_assets(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_job_video_uploads_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_job_video_uploads_size_bytes
        CHECK (size_bytes IS NULL OR size_bytes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_job_video_uploads_job_id
    ON job_video_uploads(job_id);

CREATE INDEX IF NOT EXISTS idx_job_video_uploads_asset_id
    ON job_video_uploads(asset_id);

CREATE INDEX IF NOT EXISTS idx_job_video_uploads_object_path
    ON job_video_uploads(object_path);

INSERT INTO job_video_uploads (
    asset_id,
    job_id,
    object_path,
    mime_type,
    original_filename,
    size_bytes,
    width,
    height,
    duration_seconds,
    created_at,
    updated_at
)
SELECT
    ja.id,
    ja.job_id,
    ja.object_path,
    ja.mime_type,
    ja.original_filename,
    ja.size_bytes,
    ja.width,
    ja.height,
    ja.duration_seconds,
    ja.created_at,
    NOW()
FROM job_assets ja
WHERE ja.asset_type = 'TARGET_VIDEO'
ON CONFLICT (asset_id) DO UPDATE
SET job_id = EXCLUDED.job_id,
    object_path = EXCLUDED.object_path,
    mime_type = EXCLUDED.mime_type,
    original_filename = EXCLUDED.original_filename,
    size_bytes = EXCLUDED.size_bytes,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    duration_seconds = EXCLUDED.duration_seconds,
    updated_at = NOW();

COMMIT;
