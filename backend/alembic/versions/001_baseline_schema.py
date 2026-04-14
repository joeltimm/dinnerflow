"""Baseline: stamp existing schema as starting point.

This migration represents the schema that already exists in production.
It does NOT create tables — it just establishes a revision baseline so
Alembic can track future changes.

If deploying to a fresh database, run dinnerflow_schema.sql first, then:
  alembic stamp 001

Revision ID: 001
Revises: None
Create Date: 2026-04-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline — the schema already exists. Nothing to do.
    # Tables: users, recipes, cooking_log, search_terms, shopping_list_items,
    #         user_integrations, user_sessions, recipe_sync_logs
    pass


def downgrade() -> None:
    # Cannot downgrade past the baseline.
    raise RuntimeError("Cannot downgrade past baseline schema")
