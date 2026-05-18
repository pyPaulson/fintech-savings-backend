"""add auth otp fields to users

Revision ID: 8a6d3ef2b1c4
Revises: f1e2d3c4b5a6
Create Date: 2026-04-30

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a6d3ef2b1c4"
down_revision: Union[str, None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verification_otp_hash", sa.String(), nullable=True))
    op.add_column("users", sa.Column("email_verification_otp_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("email_verification_otp_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_reset_otp_hash", sa.String(), nullable=True))
    op.add_column("users", sa.Column("password_reset_otp_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("password_reset_otp_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_reset_otp_sent_at")
    op.drop_column("users", "password_reset_otp_expires_at")
    op.drop_column("users", "password_reset_otp_hash")
    op.drop_column("users", "email_verification_otp_sent_at")
    op.drop_column("users", "email_verification_otp_expires_at")
    op.drop_column("users", "email_verification_otp_hash")
