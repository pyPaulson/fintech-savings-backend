import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_verification import (
    confirm_email_verification,
    request_email_verification,
)
from app.database.session import get_db
from app.schemas.user import EmailVerificationConfirm, EmailVerificationRequest

router = APIRouter(prefix="/auth", tags=["Auth • Verification"])
logger = logging.getLogger(__name__)


@router.post("/request-email-verification")
async def request_email_verification_endpoint(
    payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Ask for an email verification token."""
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


@router.post("/verify-email")
async def verify_email(
    payload: EmailVerificationConfirm, db: AsyncSession = Depends(get_db)
):
    """Confirm email address with verification token."""
    try:
        return await confirm_email_verification(payload, db)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error during email verification")
        raise HTTPException(
            status_code=500,
            detail="Email verification failed",
        )
