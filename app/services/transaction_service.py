import logging
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.transaction import Transaction
from app.models.enums import TransactionType, TransactionStatus
from app.services.account_service import update_account_balance

logger = logging.getLogger(__name__)


async def create_transaction(
    db: AsyncSession,
    *,
    user_id: UUID,
    account_id: UUID,
    amount: Decimal,
    transaction_type: TransactionType,
    reference: str,
    description: str | None = None,
) -> Transaction:
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero",
        )

    try:
        existing = await db.execute(
            select(Transaction).where(Transaction.reference == reference)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reference already exists",
            )

        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            amount=amount,
            type=transaction_type,
            reference=reference,
            description=description,
            status=TransactionStatus.PENDING,
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        logger.exception("Integrity error while creating transaction")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction reference already exists",
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while creating transaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating transaction",
        )
    except Exception:
        await db.rollback()
        logger.exception("Unexpected error while creating transaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while creating transaction",
        )


async def fail_transaction(db: AsyncSession, reference: str) -> Transaction:
    try:
        result = await db.execute(
            select(Transaction).where(Transaction.reference == reference)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        transaction.status = TransactionStatus.FAILED
        await db.commit()
        await db.refresh(transaction)
        return transaction
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while failing transaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating transaction",
        )


async def get_user_transactions(db: AsyncSession, user_id: UUID):
    try:
        result = await db.execute(select(Transaction).where(Transaction.user_id == user_id))
        return result.scalars().all()
    except SQLAlchemyError:
        logger.exception("Database error while fetching user transactions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching transactions",
        )


async def complete_transaction(db: AsyncSession, reference: str) -> Transaction:
    try:
        result = await db.execute(
            select(Transaction).where(Transaction.reference == reference)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if transaction.status == TransactionStatus.COMPLETED:
            return transaction

        transaction.status = TransactionStatus.COMPLETED
        await update_account_balance(db, transaction.account_id, transaction.amount)

        await db.commit()
        await db.refresh(transaction)
        return transaction
    except HTTPException:
        await db.rollback()
        raise
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while completing transaction")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating transaction",
        )
