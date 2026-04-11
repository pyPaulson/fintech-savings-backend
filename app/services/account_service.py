import logging
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.account import Account, AccountType

logger = logging.getLogger(__name__)


async def create_default_accounts(user_id: UUID, db: AsyncSession) -> list[Account]:
    """Attach default accounts to the session. Caller must commit the transaction."""
    flexi_account = Account(
        user_id=user_id, account_type=AccountType.FLEXI, currency="GHS", balance=0
    )
    emergency_account = Account(
        user_id=user_id, account_type=AccountType.EMERGENCY, currency="GHS", balance=0
    )
    db.add_all([flexi_account, emergency_account])
    return [flexi_account, emergency_account]


async def update_account_balance(
    db: AsyncSession,
    account_id: UUID,
    amount: Decimal,
) -> Account:

    try:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while fetching account")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating account balance",
        )

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        account.balance += amount
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while updating account balance")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating account balance",
        )
