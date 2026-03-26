"""Widen games.game_id from VARCHAR(255) to TEXT.

Older deployments created the column as VARCHAR(255).  This migration widens
it to TEXT so that arbitrarily long Epic Games Store URLs are stored without
truncation.  The check against information_schema makes the operation
idempotent: if the column is already TEXT the ALTER TABLE is skipped.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'free_games'
                  AND table_name   = 'games'
                  AND column_name  = 'game_id'
                  AND data_type    = 'character varying'
            ) THEN
                ALTER TABLE free_games.games ALTER COLUMN game_id TYPE TEXT;
            END IF;
        END $$
    """)


def downgrade() -> None:
    # Narrowing TEXT back to VARCHAR(255) would silently truncate values
    # longer than 255 characters, so this migration is intentionally
    # not reversible.
    pass
