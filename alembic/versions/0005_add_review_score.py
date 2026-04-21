"""Add review_score column to games table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-19

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE free_games.games
        ADD COLUMN IF NOT EXISTS review_score TEXT
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE free_games.games
        DROP COLUMN IF EXISTS review_score
    """)
