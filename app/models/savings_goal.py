import uuid

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Numeric,
    Enum,
    DateTime,
    Date,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.enums import DepositFrequency, GoalStatus


class SavingsGoal(Base):
    """
    A named savings target backed by a dedicated GOAL ledger account.
    """

    __tablename__ = "savings_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)

    target_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(8), nullable=False, default="GHS")

    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)

    deposit_frequency = Column(
        Enum(
            DepositFrequency,
            name="depositfrequency",
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=False,
    )

    installment_amount = Column(
        Numeric(12, 2),
        nullable=False,
        doc="Planned contribution per period (frequency).",
    )

    status = Column(
        Enum(
            GoalStatus,
            name="goalstatus",
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=False,
        default=GoalStatus.active,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="savings_goals")
    account = relationship("Account", back_populates="savings_goal")
