import uuid
from sqlalchemy import Column, String, ForeignKey, Numeric, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.enums import AccountType


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    account_type = Column(Enum(AccountType), nullable=False)

    currency = Column(String, default="GHS")

    balance = Column(Numeric(12, 2), default=0)

    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
