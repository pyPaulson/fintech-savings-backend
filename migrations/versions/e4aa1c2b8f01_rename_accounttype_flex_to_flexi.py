"""rename accounttype enum value flex to flexi

Revision ID: e4aa1c2b8f01
Revises: 4c5f6096a252
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e4aa1c2b8f01"
down_revision: Union[str, None] = "4c5f6096a252"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE accounttype RENAME VALUE 'flex' TO 'flexi'")


def downgrade() -> None:
    op.execute("ALTER TYPE accounttype RENAME VALUE 'flexi' TO 'flex'")
