from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import EmailVerificationConfirm, EmailVerificationRequest
from app.services.email_delivery import send_verification_email
from app.utils.email_sender import EmailSendError
from app.utils.jwt import create_email_verification_token, decode_email_verification_token

logger = logging.getLogger(__name__)

_VERIFICATION_ACK = (
    "If an account exists for this email, you will receive verification instructions shortly."
)


async def request_email_verification(payload: EmailVerificationRequest, db: AsyncSession):
    try:
        result = await db.execute(
            select(User).where(func.lower(User.email) == payload.email)
        )
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error during email verification request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during email verification",
        )

    if not user:
        return {"message": _VERIFICATION_ACK}

    if user.is_verified:
        logger.info(
            "request_email_verification: not sending mail (account already verified) user_id=%s",
            user.id,
        )
        return {"message": _VERIFICATION_ACK}

    token = create_email_verification_token({"user_id": user.id})
    logger.info(
        "request_email_verification: sending mail via Resend user_id=%s",
        user.id,
    )
    try:
        await send_verification_email(
            to_email=user.email,
            recipient_name=user.first_name,
            token=token,
        )
    except EmailSendError:
        logger.exception("Failed to send verification email user_id=%s", user.id)
    except Exception:
        logger.exception("Unexpected error sending verification email user_id=%s", user.id)
    return {"message": _VERIFICATION_ACK}


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
