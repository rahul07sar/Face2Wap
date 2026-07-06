/*
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        002_open_job_system.sql
 * Module:      Database / Migrations
 * Description:
 *
 * Adds open anonymous job system support including audit logs and IP-based
 * rate limiting tables.
 *
 * ============================================================================
 */

BEGIN;

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(64),
    action VARCHAR(128) NOT NULL,
    ip_address VARCHAR(64),
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rate_limits (
    id BIGSERIAL PRIMARY KEY,
    rate_key VARCHAR(255) NOT NULL UNIQUE,
    window_start TIMESTAMPTZ NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_rate_limits_request_count
        CHECK (request_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_job_id
    ON audit_logs(job_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action
    ON audit_logs(action);

CREATE INDEX IF NOT EXISTS idx_rate_limits_rate_key
    ON rate_limits(rate_key);

COMMIT;