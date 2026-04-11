from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account, AccountType
from app.models.enums import GoalStatus, TransactionStatus, TransactionType
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction
from app.schemas.goal import SavingsGoalCreate, SavingsGoalResponse, SavingsGoalUpdate

logger = logging.getLogger(__name__)


def _today_utc_date() -> date:
    return datetime.now(timezone.utc).date()


def _goal_to_response(goal: SavingsGoal, balance: Decimal) -> SavingsGoalResponse:
    target = goal.target_amount
    if target <= 0:
        pct = Decimal("0")
    else:
        pct = min(Decimal("100"), (balance / target) * Decimal("100"))
        pct = pct.quantize(Decimal("0.01"))

    today = _today_utc_date()
    days_left = max(0, (goal.target_date - today).days)

    return SavingsGoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        account_id=goal.account_id,
        name=goal.name,
        description=goal.description,
        target_amount=goal.target_amount,
        currency=goal.currency,
        start_date=goal.start_date,
        target_date=goal.target_date,
        deposit_frequency=goal.deposit_frequency,
        installment_amount=goal.installment_amount,
        status=goal.status,
        current_amount=balance,
        progress_percent=pct,
        days_remaining=days_left,
        created_at=goal.created_at,
    )


async def create_savings_goal(
    db: AsyncSession,
    *,
    user_id: UUID,
    payload: SavingsGoalCreate,
) -> SavingsGoalResponse:
    account = Account(
        user_id=user_id,
        account_type=AccountType.GOAL,
        currency=payload.currency,
        balance=Decimal("0"),
    )
    db.add(account)
    await db.flush()

    goal = SavingsGoal(
        user_id=user_id,
        account_id=account.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        target_amount=payload.target_amount,
        currency=payload.currency,
        start_date=payload.start_date,
        target_date=payload.target_date,
        deposit_frequency=payload.deposit_frequency,
        installment_amount=payload.installment_amount,
        status=GoalStatus.active,
    )
    db.add(goal)

    try:
        await db.commit()
        await db.refresh(goal)
        await db.refresh(account)
    except IntegrityError:
        await db.rollback()
        logger.exception("Integrity error creating savings goal")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create savings goal",
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error creating savings goal")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating savings goal",
        )

    return _goal_to_response(goal, account.balance)


async def list_savings_goals(db: AsyncSession, user_id: UUID) -> list[SavingsGoalResponse]:
    try:
        result = await db.execute(
            select(SavingsGoal, Account)
            .join(Account, Account.id == SavingsGoal.account_id)
            .where(SavingsGoal.user_id == user_id)
            .order_by(SavingsGoal.created_at.desc())
        )
        rows = result.all()
    except SQLAlchemyError:
        logger.exception("Database error listing savings goals")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while listing savings goals",
        )

    return [_goal_to_response(g, a.balance) for g, a in rows]


async def get_savings_goal(
    db: AsyncSession,
    *,
    goal_id: UUID,
    user_id: UUID,
    is_admin: bool,
) -> SavingsGoalResponse:
    try:
        result = await db.execute(
            select(SavingsGoal, Account)
            .join(Account, Account.id == SavingsGoal.account_id)
            .where(SavingsGoal.id == goal_id)
        )
        row = result.one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error fetching savings goal")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching savings goal",
        )

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found")

    goal, account = row
    if not is_admin and goal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this goal",
        )

    return _goal_to_response(goal, account.balance)


async def update_savings_goal(
    db: AsyncSession,
    *,
    goal_id: UUID,
    user_id: UUID,
    payload: SavingsGoalUpdate,
) -> SavingsGoalResponse:
    try:
        result = await db.execute(
            select(SavingsGoal, Account)
            .join(Account, Account.id == SavingsGoal.account_id)
            .where(SavingsGoal.id == goal_id)
        )
        row = result.one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error loading savings goal for update")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating savings goal",
        )

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found")

    goal, account = row
    if goal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this goal",
        )

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        goal.name = data["name"].strip()
    if "description" in data:
        goal.description = data["description"].strip() if data["description"] else None
    if "status" in data and data["status"] is not None:
        goal.status = data["status"]

    db.add(goal)
    try:
        await db.commit()
        await db.refresh(goal)
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error saving savings goal update")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating savings goal",
        )

    return _goal_to_response(goal, account.balance)


async def deposit_to_goal(
    db: AsyncSession,
    *,
    user_id: UUID,
    goal_id: UUID,
    amount: Decimal,
    description: str | None,
) -> tuple[SavingsGoalResponse, Transaction]:
    try:
        result = await db.execute(
            select(SavingsGoal, Account)
            .join(Account, Account.id == SavingsGoal.account_id)
            .where(SavingsGoal.id == goal_id)
        )
        row = result.one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error loading goal for deposit")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while processing deposit",
        )

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Savings goal not found")

    goal, account = row
    if goal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deposit to this goal",
        )

    if goal.status != GoalStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposits are only allowed for active goals",
        )

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero",
        )

    ref = f"gdep-{goal.id}-{uuid4().hex}"

    txn = Transaction(
        user_id=user_id,
        account_id=account.id,
        amount=amount,
        type=TransactionType.GOAL_DEPOSIT,
        reference=ref,
        description=description,
        status=TransactionStatus.COMPLETED,
        currency=account.currency,
    )
    account.balance += amount

    if goal.target_amount > 0 and account.balance >= goal.target_amount:
        goal.status = GoalStatus.completed

    db.add(txn)
    db.add(account)
    db.add(goal)

    try:
        await db.commit()
        await db.refresh(goal)
        await db.refresh(account)
        await db.refresh(txn)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not record deposit (duplicate reference)",
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error recording goal deposit")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while recording deposit",
        )

    return _goal_to_response(goal, account.balance), txn
