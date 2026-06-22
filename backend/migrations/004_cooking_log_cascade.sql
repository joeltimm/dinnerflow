-- Migration 004: Fix GDPR-erasure bug — cooking_log must cascade from recipes.
-- Run against the dinnerflow database:
--   docker exec -i dinner-db psql -U dinneruser -d dinnerflow < backend/migrations/004_cooking_log_cascade.sql
--
-- cooking_log links to a user only via recipe_id. Its FK to recipes had no
-- ON DELETE action (RESTRICT), so deleting a user with any cook history failed
-- with a foreign-key violation, blocking GDPR Article 17 account deletion.
-- Recreate the constraint with ON DELETE CASCADE. Idempotent.

ALTER TABLE cooking_log DROP CONSTRAINT IF EXISTS cooking_log_recipe_id_fkey;
ALTER TABLE cooking_log
  ADD CONSTRAINT cooking_log_recipe_id_fkey
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE;
