from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.enums import TransactionType, TransactionStatus


class TransactionCreate(BaseModel):
    account_id: UUID
    amount: Decimal = Field(..., gt=0)
    type: TransactionType
    reference: str | None = None
    description: str | None = None


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    type: TransactionType
    amount: Decimal
    currency: str
    status: TransactionStatus
    reference: str
    description: str | None = None

    model_config = {"from_attributes": True}
