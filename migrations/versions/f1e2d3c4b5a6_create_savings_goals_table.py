"""create savings_goals table and deposit frequency / goal status enums

Revision ID: f1e2d3c4b5a6
Revises: e4aa1c2b8f01
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, None] = "e4aa1c2b8f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'depositfrequency') THEN
                CREATE TYPE depositfrequency AS ENUM ('daily', 'weekly', 'biweekly', 'monthly');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'goalstatus') THEN
                CREATE TYPE goalstatus AS ENUM ('active', 'completed', 'paused', 'cancelled');
            END IF;
        END$$;
        """
    )
    op.create_table(
        "savings_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="GHS"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column(
            "deposit_frequency",
            postgresql.ENUM(
                "daily",
                "weekly",
                "biweekly",
                "monthly",
                name="depositfrequency",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("installment_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "completed",
                "paused",
                "cancelled",
                name="goalstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id"),
    )
    op.create_index("ix_savings_goals_user_id", "savings_goals", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_savings_goals_user_id", table_name="savings_goals")
    op.drop_table("savings_goals")
    sa.Enum(name="goalstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="depositfrequency").drop(op.get_bind(), checkfirst=True)
