/*
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        004_upload_pipeline.sql
 * Module:      Database / Migrations
 * Description:
 *
 * Adds upload pipeline fields for streaming uploads, checksum tracking,
 * validation metadata, and production-grade asset state handling.
 *
 * ============================================================================
 */

BEGIN;

ALTER TABLE job_assets
    ADD COLUMN IF NOT EXISTS sha256_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS uploaded_size_bytes BIGINT,
    ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS validation_status VARCHAR(32),
    ADD COLUMN IF NOT EXISTS validation_error TEXT,
    ADD COLUMN IF NOT EXISTS width INTEGER,
    ADD COLUMN IF NOT EXISTS height INTEGER,
    ADD COLUMN IF NOT EXISTS duration_seconds NUMERIC(12, 3);

UPDATE job_assets
SET upload_status = 'PREPARED'
WHERE upload_status = 'PENDING';

CREATE INDEX IF NOT EXISTS idx_job_assets_sha256_hash
    ON job_assets(sha256_hash);

CREATE INDEX IF NOT EXISTS idx_job_assets_validation_status
    ON job_assets(validation_status);

COMMIT;