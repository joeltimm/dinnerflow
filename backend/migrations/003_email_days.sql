-- Migration 003: per-user meal-plan email day selection
-- Run against the dinnerflow database:
--   psql -h localhost -p 5436 -U dinneruser -d dinnerflow -f backend/migrations/003_email_days.sql

-- Which weekdays a user receives meal-plan emails on.
-- ISO weekday numbers: Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6, Sun=7.
-- Default {2,6} (Tue & Sat) preserves the prior global schedule for existing users.
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS email_days integer[] NOT NULL DEFAULT '{2,6}';

-- Guard against out-of-range values (a NULL/empty array is allowed = no emails).
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_email_days_range;
ALTER TABLE users ADD CONSTRAINT chk_email_days_range
  CHECK (email_days <@ ARRAY[1,2,3,4,5,6,7]);
