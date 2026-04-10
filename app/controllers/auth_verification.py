from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import EmailVerificationConfirm, EmailVerificationRequest
from app.utils.jwt import create_email_verification_token, decode_email_verification_token

logger = logging.getLogger(__name__)


async def request_email_verification(payload: EmailVerificationRequest, db: AsyncSession):
    try:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error during email verification request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during email verification",
        )

    if not user:
        return {"message": "If the email exists, a verification link has been generated"}

    token = create_email_verification_token({"user_id": user.id})
    # In production, email the token. Returned here for dev/testing.
    return {"message": "Verification token generated", "verification_token": token}


async def confirm_email_verification(payload: EmailVerificationConfirm, db: AsyncSession):
    try:
        data = decode_email_verification_token(payload.token)
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
        logger.exception("Database error during email confirmation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during email confirmation",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    try:
        user.is_verified = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while verifying email")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify email",
        )

    return {"message": "Email verified successfully"}
