/*
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        005_upload_completion.sql
 * Module:      Database / Migrations
 * Description:
 *
 * Adds upload completion support for validated job assets.
 *
 * ============================================================================
 */

BEGIN;

ALTER TABLE job_assets
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_job_assets_completed_at
    ON job_assets(completed_at);

COMMIT;