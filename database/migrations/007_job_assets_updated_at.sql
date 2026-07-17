/*
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        007_job_assets_updated_at.sql
 * Module:      Database / Migrations
 * Description:
 *
 * Backfills the missing updated_at column on job_assets so the upload and
 * processing pipeline matches the application code.
 *
 * ============================================================================
 */

BEGIN;

ALTER TABLE job_assets
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

UPDATE job_assets
SET updated_at = COALESCE(updated_at, created_at, NOW());

COMMIT;
