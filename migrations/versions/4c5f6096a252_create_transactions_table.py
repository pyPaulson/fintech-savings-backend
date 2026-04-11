"""create transactions table

Revision ID: 4c5f6096a252
Revises: d3f6000ab8bd
Create Date: 2026-03-13 22:35:48.492443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c5f6096a252'
down_revision: Union[str, None] = 'd3f6000ab8bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactiontype') THEN
                CREATE TYPE transactiontype AS ENUM ('deposit', 'withdrawal', 'transfer', 'goal_deposit', 'goal_withdrawal');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transactionstatus') THEN
                CREATE TYPE transactionstatus AS ENUM ('pending', 'completed', 'failed', 'reversed');
            END IF;
        END$$;
        """
    )

    op.create_table(
        'transactions',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('account_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('type', sa.dialects.postgresql.ENUM('deposit', 'withdrawal', 'transfer', 'goal_deposit', 'goal_withdrawal', name='transactiontype', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(), nullable=False, server_default='GHS'),
        sa.Column('status', sa.dialects.postgresql.ENUM('pending', 'completed', 'failed', 'reversed', name='transactionstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('reference', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_account_id', 'transactions', ['account_id'])
    op.create_index('ix_transactions_reference', 'transactions', ['reference'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_transactions_reference', table_name='transactions')
    op.drop_index('ix_transactions_account_id', table_name='transactions')
    op.drop_index('ix_transactions_user_id', table_name='transactions')
    op.drop_table('transactions')
    sa.Enum(name='transactiontype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='transactionstatus').drop(op.get_bind(), checkfirst=True)
