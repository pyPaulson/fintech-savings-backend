"""create accounts table

Revision ID: f608f77543e5
Revises: 77d262f84793
Create Date: 2026-03-12 12:41:00.360434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f608f77543e5'
down_revision: Union[str, None] = '77d262f84793'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum only if it does not already exist to avoid DuplicateObjectError
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'accounttype') THEN
                CREATE TYPE accounttype AS ENUM ('flex', 'emergency', 'goal', 'locked');
            END IF;
        END$$;
        """
    )

    op.create_table(
        'accounts',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('account_type', sa.dialects.postgresql.ENUM('flex', 'emergency', 'goal', 'locked', name='accounttype', create_type=False), nullable=False),
        sa.Column('currency', sa.String(), nullable=True, server_default='GHS'),
        sa.Column('balance', sa.Numeric(12, 2), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('accounts')
    sa.Enum(name='accounttype').drop(op.get_bind(), checkfirst=True)
