from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.controllers.user import create_user
from app.models.user import User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


async def create_admin(user: UserCreate, db: AsyncSession) -> User:
    return await create_user(user, db, as_admin=True)


async def admins_exist(db: AsyncSession) -> bool:
    try:
        result = await db.execute(select(User).where(User.is_admin.is_(True)))
        return result.scalars().first() is not None
    except SQLAlchemyError:
        logger.exception("Database error while checking for existing admins")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while checking admins",
        )


async def list_users(db: AsyncSession) -> list[User]:
    try:
        result = await db.execute(select(User))
        return result.scalars().all()
    except SQLAlchemyError:
        logger.exception("Database error while listing users")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching users",
        )
