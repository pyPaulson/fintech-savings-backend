import uuid
from sqlalchemy import Column, String, ForeignKey, Numeric, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.enums import TransactionType, TransactionStatus


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    type = Column(
        Enum(
            TransactionType,
            name="transactiontype",
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    currency = Column(
        String,
        default="GHS",
        nullable=False,
    )

    status = Column(
        Enum(
            TransactionStatus,
            name="transactionstatus",
            native_enum=True,
            values_callable=lambda obj: [e.value for e in obj],
            create_type=False,
        ),
        default=TransactionStatus.PENDING,
        nullable=False,
    )

    reference = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    description = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships

    user = relationship("User", back_populates="transactions")

    account = relationship("Account", back_populates="transactions")
