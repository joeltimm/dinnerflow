-- Migration 006: Per-user meal-plan delivery time + timezone.
-- Run against the dinnerflow database:
--   docker exec -i dinner-db psql -U dinneruser -d dinnerflow < backend/migrations/006_user_schedule.sql
--
-- Previously meal-plan emails fired at a single hardcoded 10:30 America/Chicago for
-- everyone. These columns let each user pick their own local delivery time + zone.
-- last_meal_plan_sent_at prevents duplicate sends now that beat fires every minute.
-- Idempotent.

ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone_name text NOT NULL DEFAULT 'America/Chicago';
ALTER TABLE users ADD COLUMN IF NOT EXISTS meal_plan_hour integer NOT NULL DEFAULT 10;
ALTER TABLE users ADD COLUMN IF NOT EXISTS meal_plan_minute integer NOT NULL DEFAULT 30;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_meal_plan_sent_at timestamptz;

DO $$ BEGIN
  ALTER TABLE users ADD CONSTRAINT chk_meal_plan_hour CHECK (meal_plan_hour BETWEEN 0 AND 23);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE users ADD CONSTRAINT chk_meal_plan_minute CHECK (meal_plan_minute BETWEEN 0 AND 59);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
