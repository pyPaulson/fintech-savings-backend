from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.services.account_service import create_default_accounts
from app.services.email_delivery import send_verification_email
from app.schemas.user import UserCreate, UserUpdate
from app.utils.email_sender import EmailSendError
from app.utils.otp import expires_in_minutes, generate_otp, hash_otp, utc_now
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
        result = await db.execute(
            select(User).where(func.lower(User.email) == user.email)
        )
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
        await db.flush()
        if not as_admin:
            await create_default_accounts(new_user.id, db)
        await db.commit()
        await db.refresh(new_user)

        if not as_admin and not new_user.is_verified:
            try:
                otp = generate_otp()
                new_user.email_verification_otp_hash = hash_otp(
                    purpose="email_verification",
                    email=new_user.email,
                    otp=otp,
                )
                new_user.email_verification_otp_expires_at = expires_in_minutes(
                    settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES
                )
                new_user.email_verification_otp_sent_at = utc_now()
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                await send_verification_email(
                    to_email=new_user.email,
                    recipient_name=new_user.first_name,
                    otp=otp,
                )
            except EmailSendError:
                logger.exception(
                    "Failed to send verification email after signup user_id=%s",
                    new_user.id,
                )
            except SQLAlchemyError:
                await db.rollback()
                logger.exception(
                    "Failed to save verification OTP after signup user_id=%s",
                    new_user.id,
                )
            except Exception:
                logger.exception(
                    "Unexpected error sending verification email after signup user_id=%s",
                    new_user.id,
                )

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
