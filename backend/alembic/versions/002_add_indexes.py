"""Add performance indexes for scalability.

Converted from migrations/001_add_indexes.sql into Alembic.

Revision ID: 002
Revises: 001
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes (user_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_recipes_user_favorites "
        "ON recipes (user_id, is_favorite) WHERE is_favorite = true"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_recipes_user_created "
        "ON recipes (user_id, created_at DESC)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions (expires_at)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_shopping_user_id "
        "ON shopping_list_items (user_id, is_checked, created_at DESC)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_cooking_log_recipe_id ON cooking_log (recipe_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_logs_user_id ON recipe_sync_logs (user_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_sync_logs_user_id")
    op.execute("DROP INDEX IF EXISTS idx_cooking_log_recipe_id")
    op.execute("DROP INDEX IF EXISTS idx_shopping_user_id")
    op.execute("DROP INDEX IF EXISTS idx_sessions_expires")
    op.execute("DROP INDEX IF EXISTS idx_sessions_user_id")
    op.execute("DROP INDEX IF EXISTS idx_recipes_user_created")
    op.execute("DROP INDEX IF EXISTS idx_recipes_user_favorites")
    op.execute("DROP INDEX IF EXISTS idx_recipes_user_id")
