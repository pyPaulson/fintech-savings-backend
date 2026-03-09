"""create users table

Revision ID: 37d16790071d
Revises: 7930930986a0
Create Date: 2026-03-09 15:45:33.364054

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '37d16790071d'
down_revision: Union[str, None] = '7930930986a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Intentionally no-op.
    # This revision was auto-generated while DB was behind head and duplicated
    # the initial users-table creation already done in 7930930986a0.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # Intentionally no-op.
    pass
