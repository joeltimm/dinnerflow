-- Migration 001: Add missing indexes for scalability
-- Run against the dinnerflow database:
--   psql -h localhost -p 5436 -U dinneruser -d dinnerflow -f backend/migrations/001_add_indexes.sql

-- recipes: most queries filter by user_id
CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes (user_id);

-- recipes: instant-ideas and meal plan load favorites per user
CREATE INDEX IF NOT EXISTS idx_recipes_user_favorites ON recipes (user_id, is_favorite)
    WHERE is_favorite = true;

-- recipes: recipe list sorted by created_at
CREATE INDEX IF NOT EXISTS idx_recipes_user_created ON recipes (user_id, created_at DESC);

-- user_sessions: session lookup by token (PK covers this, but add user_id index for cleanup)
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions (user_id);

-- user_sessions: cleanup job deletes expired sessions
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions (expires_at);

-- shopping_list_items: list items per user, sorted by checked/created
CREATE INDEX IF NOT EXISTS idx_shopping_user_id ON shopping_list_items (user_id, is_checked, created_at DESC);

-- cooking_log: dashboard joins cooking_log to recipes
CREATE INDEX IF NOT EXISTS idx_cooking_log_recipe_id ON cooking_log (recipe_id);

-- recipe_sync_logs: lookup by user
CREATE INDEX IF NOT EXISTS idx_sync_logs_user_id ON recipe_sync_logs (user_id);
