import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_verification import (
    confirm_email_verification,
    request_email_verification,
)
from app.database.session import get_db
from app.schemas.user import AuthSessionResponse, EmailVerificationConfirm, EmailVerificationRequest
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Auth • Verification"])
logger = logging.getLogger(__name__)


@router.post("/request-email-verification")
async def request_email_verification_endpoint(
    payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Request a verification OTP sent to the given email when an account exists."""
    try:
        return await request_email_verification(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during email verification request")
        raise HTTPException(
            status_code=500,
            detail="Unable to request verification",
        )


@router.post("/verify-email", response_model=AuthSessionResponse)
async def verify_email(
    payload: EmailVerificationConfirm,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Confirm email address with a six-digit OTP (JSON body)."""
    try:
        result = await confirm_email_verification(payload, db)
        response.set_cookie(
            key="access_token",
            value=result["access_token"],
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during email verification")
        raise HTTPException(
            status_code=500,
            detail="Email verification failed",
        )
