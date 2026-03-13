import logging
from uuid import UUID, uuid4
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from app.models.account import Account
from app.models.transaction import Transaction
from app.models.enums import TransactionType
from app.services.transaction_service import (
    complete_transaction as svc_complete_transaction,
    create_transaction as svc_create_transaction,
    fail_transaction as svc_fail_transaction,
    get_user_transactions as svc_get_user_transactions,
)

logger = logging.getLogger(__name__)


async def _ensure_account_access(account: Account, user_id: UUID, is_admin: bool):
    if is_admin:
        return
    if account.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account",
        )


async def create_transaction_for_user(
    db: AsyncSession,
    *,
    user_id: UUID,
    is_admin: bool,
    account_id: UUID,
    amount: Decimal,
    transaction_type: TransactionType,
    reference: str | None,
    description: str | None,
) -> Transaction:
    try:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while checking account for transaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while validating account",
        )

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    await _ensure_account_access(account, user_id, is_admin)

    ref_value = reference or str(uuid4())

    return await svc_create_transaction(
        db,
        user_id=user_id,
        account_id=account_id,
        amount=amount,
        transaction_type=transaction_type,
        reference=ref_value,
        description=description,
    )


async def list_transactions_for_user(db: AsyncSession, user_id: UUID):
    return await svc_get_user_transactions(db, user_id)


async def complete_transaction_admin(db: AsyncSession, reference: str) -> Transaction:
    return await svc_complete_transaction(db, reference)


async def fail_transaction_admin(db: AsyncSession, reference: str) -> Transaction:
    return await svc_fail_transaction(db, reference)
