import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth import get_current_user
from app.controllers.transaction import (
    complete_transaction_admin,
    create_transaction_for_user,
    fail_transaction_admin,
    list_transactions_for_user,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])
logger = logging.getLogger(__name__)


async def _current_user_dependency(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    return await get_current_user(request, db)


def _ensure_admin(user: User):
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction_endpoint(
    payload: TransactionCreate,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a transaction for the authenticated user (reference auto-generates if omitted).
    """
    try:
        txn = await create_transaction_for_user(
            db,
            user_id=current_user.id,
            is_admin=current_user.is_admin,
            account_id=payload.account_id,
            amount=payload.amount,
            transaction_type=payload.type,
            reference=payload.reference,
            description=payload.description,
        )
        return txn
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in create_transaction_endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction",
        )


@router.get("/", response_model=list[TransactionResponse])
async def list_my_transactions(
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    List transactions for the authenticated user.
    """
    try:
        return await list_transactions_for_user(db, current_user.id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in list_my_transactions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transactions",
        )


@router.post("/{reference}/complete", response_model=TransactionResponse)
async def complete_transaction(
    reference: str,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a transaction as completed (admin only).
    """
    _ensure_admin(current_user)
    try:
        return await complete_transaction_admin(db, reference)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in complete_transaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete transaction",
        )


@router.post("/{reference}/fail", response_model=TransactionResponse)
async def fail_transaction(
    reference: str,
    current_user: User = Depends(_current_user_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a transaction as failed (admin only).
    """
    _ensure_admin(current_user)
    try:
        return await fail_transaction_admin(db, reference)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in fail_transaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fail transaction",
        )
