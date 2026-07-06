/*
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        003_upload_system.sql
 * Module:      Database / Migrations
 * Description:
 *
 * Extends job asset tracking for upload preparation, upload expiry,
 * storage provider support, and upload completion tracking.
 *
 * ============================================================================
 */

BEGIN;

ALTER TABLE job_assets
    ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(32) NOT NULL DEFAULT 'local',
    ADD COLUMN IF NOT EXISTS upload_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    ADD COLUMN IF NOT EXISTS upload_expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS original_filename TEXT;

CREATE INDEX IF NOT EXISTS idx_job_assets_upload_status
    ON job_assets(upload_status);

CREATE INDEX IF NOT EXISTS idx_job_assets_upload_expires_at
    ON job_assets(upload_expires_at);

COMMIT;