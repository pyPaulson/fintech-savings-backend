from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.user import User
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetOtpVerifyRequest,
    PasswordResetRequest,
)
from app.services.email_delivery import (
    send_password_reset_email,
    send_password_reset_success_email,
)
from app.utils.email_sender import EmailSendError
from app.utils.otp import expires_in_minutes, generate_otp, hash_otp, utc_now, verify_otp
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

_PASSWORD_RESET_ACK = (
    "If an account exists for this email, you will receive a password reset code shortly."
)


async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession):
    try:
        result = await db.execute(
            select(User).where(func.lower(User.email) == payload.email)
        )
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error during password reset request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during password reset",
        )

    if not user or not user.is_active:
        return {"message": _PASSWORD_RESET_ACK}

    now = utc_now()
    sent_at = user.password_reset_otp_sent_at
    if sent_at and sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=now.tzinfo)
    if sent_at:
        elapsed_seconds = (now - sent_at).total_seconds()
        if elapsed_seconds < settings.OTP_RESEND_COOLDOWN_SECONDS:
            retry_after = settings.OTP_RESEND_COOLDOWN_SECONDS - int(elapsed_seconds)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {retry_after} seconds before requesting another code.",
            )

    otp = generate_otp()
    user.password_reset_otp_hash = hash_otp(
        purpose="password_reset",
        email=user.email,
        otp=otp,
    )
    user.password_reset_otp_expires_at = expires_in_minutes(
        settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES
    )
    user.password_reset_otp_sent_at = now

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while saving password reset OTP")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not prepare password reset",
        )

    try:
        await send_password_reset_email(
            to_email=user.email,
            recipient_name=user.first_name,
            otp=otp,
        )
    except EmailSendError:
        logger.exception("Failed to send password reset email user_id=%s", user.id)
    except Exception:
        logger.exception("Unexpected error sending password reset email user_id=%s", user.id)
    return {"message": _PASSWORD_RESET_ACK}


async def verify_password_reset_otp(payload: PasswordResetOtpVerifyRequest, db: AsyncSession):
    try:
        result = await db.execute(
            select(User).where(func.lower(User.email) == payload.email)
        )
        user = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error during password reset OTP verification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during password reset verification",
        )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code",
        )

    expires_at = user.password_reset_otp_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=utc_now().tzinfo)
    if not expires_at or expires_at < utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired",
        )

    if not verify_otp(
        purpose="password_reset",
        email=user.email,
        otp=payload.otp,
        otp_hash=user.password_reset_otp_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code",
        )

    return {"message": "OTP verified successfully"}


async def reset_password(payload: PasswordResetConfirm, db: AsyncSession):
    try:
        result = await db.execute(
            select(User).where(func.lower(User.email) == payload.email)
        )
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
            detail="Invalid reset code",
        )

    expires_at = user.password_reset_otp_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=utc_now().tzinfo)
    if not expires_at or expires_at < utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired",
        )

    if not verify_otp(
        purpose="password_reset",
        email=user.email,
        otp=payload.otp,
        otp_hash=user.password_reset_otp_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset code",
        )

    try:
        user.password_hash = hash_password(payload.new_password)
        user.is_verified = True
        user.password_reset_otp_hash = None
        user.password_reset_otp_expires_at = None
        user.password_reset_otp_sent_at = None
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

    try:
        await send_password_reset_success_email(
            to_email=user.email,
            recipient_name=user.first_name,
        )
    except EmailSendError:
        logger.exception("Failed to send password reset success email user_id=%s", user.id)
    except Exception:
        logger.exception("Unexpected error sending password reset success email user_id=%s", user.id)

    return {"message": "Password reset successful"}
