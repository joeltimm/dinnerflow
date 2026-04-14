-- Migration 002: Compliance — email consent tracking + data retention index
-- Run against the dinnerflow database:
--   psql -h localhost -p 5436 -U dinneruser -d dinnerflow -f backend/migrations/002_compliance.sql

-- Email consent: opt-in tracking for meal plan emails (GDPR / CAN-SPAM)
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_consent boolean NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_consent_date timestamp with time zone;

-- Index for scheduled email fan-out: only select consented users
CREATE INDEX IF NOT EXISTS idx_users_email_consent ON users (id) WHERE email_consent = true;

-- Index for data retention cleanup on search_terms
CREATE INDEX IF NOT EXISTS idx_search_terms_created ON search_terms (created_at);

-- Index for data retention cleanup on recipe_sync_logs (idx_sync_logs_time exists but on synced_at — keep both)
