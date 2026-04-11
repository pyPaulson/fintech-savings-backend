import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.account import Account

logger = logging.getLogger(__name__)


async def get_account(account_id: UUID, db: AsyncSession) -> Account:
    try:
        result = await db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while fetching account")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching account",
        )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account


async def get_user_accounts(user_id: UUID, db: AsyncSession):
    try:
        result = await db.execute(select(Account).where(Account.user_id == user_id))
        return result.scalars().all()
    except SQLAlchemyError:
        logger.exception("Database error while fetching user accounts")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching accounts",
        )
