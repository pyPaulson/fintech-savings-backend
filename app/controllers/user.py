from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.services.account_service import create_default_accounts
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


def _resolve_unique_conflict(exc: IntegrityError) -> str:
    error_text = str(exc.orig).lower() if exc.orig else ""
    if "email" in error_text:
        return "Email already registered"
    if "phone_number" in error_text or "phone" in error_text:
        return "Phone number already registered"
    return "A unique field already exists"


async def create_user(user: UserCreate, db: AsyncSession, *, as_admin: bool = False) -> User:
    try:
        result = await db.execute(select(User).where(User.email == user.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        try:
            password_hash = hash_password(user.password)
        except Exception:
            logger.exception("Password hashing failed during user creation")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process password",
            )

        new_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=password_hash,
            phone_number=user.phone_number,
            gender=user.gender,
            date_of_birth=user.date_of_birth,
            is_verified=True if as_admin else False,
            is_admin=True if as_admin else False,
        )

        db.add(new_user)
        await create_default_accounts(new_user.id, db) 
        await db.commit()
        await db.refresh(new_user)
        return new_user

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as exc:
        await db.rollback()
        detail = _resolve_unique_conflict(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while creating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating user",
        )
    except Exception:
        await db.rollback()
        logger.exception("Unexpected error while creating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while creating user",
        )


async def update_user_profile(user: User, updates: UserUpdate, db: AsyncSession) -> User:
    update_data = updates.dict(exclude_unset=True)
    if not update_data:
        return user

    try:
        for attr, value in update_data.items():
            setattr(user, attr, value)

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as exc:
        await db.rollback()
        detail = _resolve_unique_conflict(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while updating user profile")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating profile",
        )
    except Exception:
        await db.rollback()
        logger.exception("Unexpected error while updating user profile")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while updating profile",
        )


async def get_user_by_id(user_id, db: AsyncSession) -> User:
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while fetching user by id")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching user",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def deactivate_user(user: User, db: AsyncSession) -> User:
    try:
        user.is_active = False
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while deactivating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deactivating user",
        )
    except Exception:
        await db.rollback()
        logger.exception("Unexpected error while deactivating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while deactivating user",
        )
