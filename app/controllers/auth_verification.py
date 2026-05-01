from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.user import User
from app.schemas.user import AuthSessionResponse, EmailVerificationConfirm, EmailVerificationRequest, UserResponse
from app.services.email_delivery import (
    send_email_verified_success_email,
    send_verification_email,
)
from app.utils.email_sender import EmailSendError
from app.utils.jwt import create_access_token
from app.utils.otp import expires_in_minutes, generate_otp, hash_otp, utc_now, verify_otp

logger = logging.getLogger(__name__)

_VERIFICATION_ACK = (
    "If an account exists for this email, you will receive a verification code shortly."
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

    now = utc_now()
    sent_at = user.email_verification_otp_sent_at
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
    user.email_verification_otp_hash = hash_otp(
        purpose="email_verification",
        email=user.email,
        otp=otp,
    )
    user.email_verification_otp_expires_at = expires_in_minutes(
        settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES
    )
    user.email_verification_otp_sent_at = now

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while saving email verification OTP")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not prepare email verification",
        )

    logger.info("request_email_verification: sending OTP via Brevo user_id=%s", user.id)
    try:
        await send_verification_email(
            to_email=user.email,
            recipient_name=user.first_name,
            otp=otp,
        )
    except EmailSendError:
        logger.exception("Failed to send verification email user_id=%s", user.id)
    except Exception:
        logger.exception("Unexpected error sending verification email user_id=%s", user.id)
    return {"message": _VERIFICATION_ACK}


async def confirm_email_verification(payload: EmailVerificationConfirm, db: AsyncSession):
    try:
        result = await db.execute(
            select(User).where(func.lower(User.email) == payload.email)
        )
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
            detail="Invalid verification code",
        )

    if user.is_verified:
        access_token = create_access_token({"user_id": user.id})
        user_payload = UserResponse.model_validate(user)
        return AuthSessionResponse(
            message="Email already verified",
            access_token=access_token,
            user=user_payload,
        ).model_dump()

    expires_at = user.email_verification_otp_expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=utc_now().tzinfo)
    if not expires_at or expires_at < utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired",
        )

    if not verify_otp(
        purpose="email_verification",
        email=user.email,
        otp=payload.otp,
        otp_hash=user.email_verification_otp_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    try:
        user.is_verified = True
        user.email_verification_otp_hash = None
        user.email_verification_otp_expires_at = None
        user.email_verification_otp_sent_at = None
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

    access_token = create_access_token({"user_id": user.id})
    user_payload = UserResponse.model_validate(user)
    try:
        await send_email_verified_success_email(
            to_email=user.email,
            recipient_name=user.first_name,
        )
    except EmailSendError:
        logger.exception("Failed to send email verified success email user_id=%s", user.id)
    except Exception:
        logger.exception("Unexpected error sending email verified success email user_id=%s", user.id)

    return AuthSessionResponse(
        message="Email verified successfully",
        access_token=access_token,
        user=user_payload,
    ).model_dump()
