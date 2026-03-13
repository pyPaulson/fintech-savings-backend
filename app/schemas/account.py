from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel

from app.models.account import AccountType


class AccountResponse(BaseModel):
    id: UUID
    user_id: UUID
    account_type: AccountType
    currency: str
    balance: Decimal
    is_active: bool

    model_config = {"from_attributes": True}
