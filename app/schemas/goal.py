from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import DepositFrequency, GoalStatus


class SavingsGoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="What you are saving for")
    description: Optional[str] = Field(None, max_length=2000)
    target_amount: Decimal = Field(..., gt=0, description="Amount you want to reach")
    currency: str = Field(default="GHS", min_length=3, max_length=8)
    start_date: date = Field(..., description="When the plan starts")
    target_date: date = Field(..., description="When you want to hit the target (defines the horizon)")
    deposit_frequency: DepositFrequency = Field(
        ...,
        description="How often you plan to contribute (daily, weekly, biweekly, monthly)",
    )
    installment_amount: Decimal = Field(
        ...,
        gt=0,
        description="How much you intend to set aside each period (matches deposit_frequency)",
    )

    @model_validator(mode="after")
    def dates_make_sense(self) -> SavingsGoalCreate:
        if self.target_date <= self.start_date:
            raise ValueError("target_date must be after start_date")
        return self


class SavingsGoalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[GoalStatus] = None


class GoalDepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount to move into this goal")
    description: Optional[str] = Field(None, max_length=500, description="Optional note for your records")


class SavingsGoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    name: str
    description: Optional[str]
    target_amount: Decimal
    currency: str
    start_date: date
    target_date: date
    deposit_frequency: DepositFrequency
    installment_amount: Decimal
    status: GoalStatus
    current_amount: Decimal = Field(
        ...,
        description="Balance currently allocated to this goal",
    )
    progress_percent: Decimal = Field(
        ...,
        description="0–100, capped at 100",
    )
    days_remaining: int = Field(..., ge=0)
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GoalDepositResponse(BaseModel):
    goal: SavingsGoalResponse
    transaction_id: UUID
    reference: str
    amount: Decimal
