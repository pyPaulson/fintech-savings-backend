import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_password import (
    request_password_reset,
    reset_password,
    verify_password_reset_otp,
)
from app.database.session import get_db
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetOtpVerifyRequest,
    PasswordResetRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth • Password"])
logger = logging.getLogger(__name__)


@router.post("/forgot-password")
async def forgot_password(
    payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)
):
    """
    Initiate password reset. A six-digit OTP is sent via email when the account exists.
    """
    try:
        return await request_password_reset(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during forgot password")
        raise HTTPException(
            status_code=500,
            detail="Unable to start password reset",
        )


@router.post("/verify-reset-otp")
async def verify_reset_otp_endpoint(
    payload: PasswordResetOtpVerifyRequest, db: AsyncSession = Depends(get_db)
):
    """
    Verify a password reset OTP before allowing the user to set a new password.
    """
    try:
        return await verify_password_reset_otp(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during reset OTP verification")
        raise HTTPException(
            status_code=500,
            detail="OTP verification failed",
        )


@router.post("/reset-password")
async def reset_password_endpoint(
    payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)
):
    """
    Complete password reset with a valid OTP.
    """
    try:
        return await reset_password(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during password reset")
        raise HTTPException(
            status_code=500,
            detail="Password reset failed",
        )
