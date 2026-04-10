from __future__ import annotations

import logging

from fastapi import HTTPException, status 
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import PasswordResetConfirm, PasswordResetRequest
from app.utils.jwt import create_password_reset_token, decode_password_reset_token
from app.utils.security import hash_password

logger = logging.getLogger(__name__)


async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession):
    try:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error during password reset request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during password reset",
        )

    if not user:
        return {"message": "If the email exists, a reset link has been generated"}

    token = create_password_reset_token({"user_id": user.id})
    # In production, email the token. Returned here for dev/testing.
    return {"message": "Password reset token generated", "reset_token": token}


async def reset_password(payload: PasswordResetConfirm, db: AsyncSession):
    try:
        data = decode_password_reset_token(payload.token)
        user_id = data["user_id"]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error during password reset")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during password reset",
        )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    try:
        user.password_hash = hash_password(payload.new_password)
        user.is_verified = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while saving new password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reset password",
        )

    return {"message": "Password reset successful"}
