import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import goal as goal_controller
from app.controllers.auth import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.goal import (
    GoalDepositRequest,
    GoalDepositResponse,
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)

router = APIRouter(prefix="/goals", tags=["Goals • Savings"])
logger = logging.getLogger(__name__)


async def _current_user_dependency(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    return await get_current_user(request, db)


@router.post(
    "/",
    response_model=SavingsGoalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_goal(
    payload: SavingsGoalCreate,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a savings goal: a dedicated goal account, target amount, timeline, and how often
    you plan to contribute (installment amount + frequency).
    """
    try:
        return await goal_controller.create_goal(db, current_user.id, payload)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error creating savings goal")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create savings goal",
        )


@router.get("/", response_model=list[SavingsGoalResponse])
async def list_goals(
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """List your savings goals with live balance and progress."""
    try:
        return await goal_controller.list_my_goals(db, current_user.id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error listing savings goals")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list savings goals",
        )


@router.get("/{goal_id}", response_model=SavingsGoalResponse)
async def get_goal(
    goal_id: UUID,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """Get one goal (admins can read any goal)."""
    try:
        return await goal_controller.get_goal(
            db, goal_id, current_user.id, current_user.is_admin
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error fetching savings goal")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch savings goal",
        )


@router.patch("/{goal_id}", response_model=SavingsGoalResponse)
async def update_goal(
    goal_id: UUID,
    payload: SavingsGoalUpdate,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """Rename, pause, cancel, or mark completed (status) when you control the goal."""
    try:
        return await goal_controller.update_goal(db, goal_id, current_user.id, payload)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error updating savings goal")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update savings goal",
        )


@router.post(
    "/{goal_id}/deposit",
    response_model=GoalDepositResponse,
    status_code=status.HTTP_201_CREATED,
)
async def deposit_to_goal(
    goal_id: UUID,
    payload: GoalDepositRequest,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Deposit into your goal. Credits the goal ledger immediately and records a completed
    `goal_deposit` transaction. The goal auto-completes when the balance reaches the target.
    """
    try:
        return await goal_controller.deposit(db, goal_id, current_user.id, payload)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error depositing to savings goal")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deposit to savings goal",
        )
