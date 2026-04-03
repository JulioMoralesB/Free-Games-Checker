"""Add last_notification table to store the most recently sent game batch.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-02

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS free_games.last_notification (
            id    INTEGER PRIMARY KEY,
            games TEXT NOT NULL
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS free_games.last_notification")
