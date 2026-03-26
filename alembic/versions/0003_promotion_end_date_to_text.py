"""Convert games.promotion_end_date from TIMESTAMP to TEXT (ISO-8601 UTC).

Older deployments stored the promotion end date as
``TIMESTAMP WITHOUT TIME ZONE``.  This migration converts it to ``TEXT``,
preserving the ISO-8601 format (``YYYY-MM-DD"T"HH24:MI:SS.MS"Z"``) that the
scraper has always returned.  The check against information_schema makes the
operation idempotent: if the column is already TEXT the ALTER TABLE is skipped.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
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
                  AND column_name  = 'promotion_end_date'
                  AND data_type    = 'timestamp without time zone'
            ) THEN
                ALTER TABLE free_games.games
                ALTER COLUMN promotion_end_date TYPE TEXT
                USING TO_CHAR(
                    promotion_end_date AT TIME ZONE 'UTC',
                    'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'
                );
            END IF;
        END $$
    """)


def downgrade() -> None:
    # Converting TEXT back to TIMESTAMP would fail for NULL values and for any
    # string that does not parse as a valid timestamp, so this migration is
    # intentionally not reversible.
    pass
