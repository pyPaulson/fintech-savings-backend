from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.goal import (
    GoalDepositRequest,
    GoalDepositResponse,
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)
from app.services import goal_service


async def create_goal(
    db: AsyncSession,
    user_id: UUID,
    payload: SavingsGoalCreate,
) -> SavingsGoalResponse:
    return await goal_service.create_savings_goal(db, user_id=user_id, payload=payload)


async def list_my_goals(db: AsyncSession, user_id: UUID) -> list[SavingsGoalResponse]:
    return await goal_service.list_savings_goals(db, user_id)


async def get_goal(
    db: AsyncSession,
    goal_id: UUID,
    user_id: UUID,
    is_admin: bool,
) -> SavingsGoalResponse:
    return await goal_service.get_savings_goal(
        db, goal_id=goal_id, user_id=user_id, is_admin=is_admin
    )


async def update_goal(
    db: AsyncSession,
    goal_id: UUID,
    user_id: UUID,
    payload: SavingsGoalUpdate,
) -> SavingsGoalResponse:
    return await goal_service.update_savings_goal(
        db, goal_id=goal_id, user_id=user_id, payload=payload
    )


async def deposit(
    db: AsyncSession,
    goal_id: UUID,
    user_id: UUID,
    payload: GoalDepositRequest,
) -> GoalDepositResponse:
    goal, txn = await goal_service.deposit_to_goal(
        db,
        user_id=user_id,
        goal_id=goal_id,
        amount=payload.amount,
        description=payload.description,
    )
    return GoalDepositResponse(
        goal=goal,
        transaction_id=txn.id,
        reference=txn.reference,
        amount=txn.amount,
    )
