"""Add store column to games table and migrate game_id to prefixed format.

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-20

Adds a ``store`` column (TEXT, NOT NULL, DEFAULT 'epic') to
``free_games.games`` so that every row carries an explicit origin store.

Also updates existing ``game_id`` values to use the ``<store>:<url>``
prefixed format (e.g. ``epic:https://...``) so that IDs remain unique
even when multiple stores share a similar URL structure.

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the store column with a safe default so existing rows are valid.
    op.execute("""
        ALTER TABLE free_games.games
        ADD COLUMN IF NOT EXISTS store TEXT NOT NULL DEFAULT 'epic'
    """)

    # 2. Migrate existing game_id values that don't already carry a store
    #    prefix.  The only store stored so far is Epic, so all un-prefixed IDs
    #    get the ``epic:`` prefix.  Match against known store prefixes rather
    #    than any colon so existing URL-based IDs (https://...) are migrated.
    op.execute("""
        UPDATE free_games.games
        SET game_id = 'epic:' || game_id,
            store   = 'epic'
        WHERE game_id !~ '^(epic|steam|gog|humble):'
    """)


def downgrade() -> None:
    # Stripping all store prefixes would collapse ``epic:<url>`` and
    # ``steam:<url>`` to the same bare URL, violating the UNIQUE constraint.
    # The pre-0006 schema only stored Epic games, so non-epic rows are
    # removed first.  This is intentionally destructive: downgrade means
    # reverting to single-store support.
    op.execute("""
        DELETE FROM free_games.games
        WHERE game_id ~ '^(steam|gog|humble):'
    """)

    # Strip the single-segment store prefix so remaining game_id values match
    # the pre-0006 format.  REGEXP_REPLACE removes only the leading
    # ``<store>:`` token, leaving any further colons in the URL intact.
    op.execute("""
        UPDATE free_games.games
        SET game_id = REGEXP_REPLACE(game_id, '^(epic|steam|gog|humble):', '')
        WHERE game_id ~ '^(epic|steam|gog|humble):'
    """)

    op.execute("""
        ALTER TABLE free_games.games
        DROP COLUMN IF EXISTS store
    """)
