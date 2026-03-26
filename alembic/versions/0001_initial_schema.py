"""Initial schema: create free_games schema and games table.

Revision ID: 0001
Revises:
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the schema if it does not already exist (idempotent).
    op.execute("CREATE SCHEMA IF NOT EXISTS free_games")

    # Create the games table with the final column types.
    # IF NOT EXISTS makes this safe against deployments that already ran the
    # legacy init_db() table-creation logic.
    op.execute("""
        CREATE TABLE IF NOT EXISTS free_games.games (
            id                 SERIAL PRIMARY KEY,
            game_id            TEXT UNIQUE NOT NULL,
            title              TEXT NOT NULL,
            link               TEXT NOT NULL,
            description        TEXT,
            thumbnail          TEXT,
            promotion_end_date TEXT
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS free_games.games")
    op.execute("DROP SCHEMA IF EXISTS free_games")
