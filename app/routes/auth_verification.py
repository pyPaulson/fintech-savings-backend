import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_verification import (
    confirm_email_verification,
    request_email_verification,
)
from app.core.config import settings
from app.database.session import get_db
from app.schemas.user import EmailVerificationConfirm, EmailVerificationRequest

router = APIRouter(prefix="/auth", tags=["Auth • Verification"])
logger = logging.getLogger(__name__)


def _frontend_verify_url(*, verify: str) -> str:
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    path = settings.EMAIL_VERIFICATION_PATH
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}?{urlencode({'verify': verify})}"


@router.post("/request-email-verification")
async def request_email_verification_endpoint(
    payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)
):
    """Request a verification link sent to the given email when an account exists."""
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
    """Confirm email address with verification token (JSON body)."""
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


@router.get("/verify-email/click")
async def verify_email_click(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    One-click verification from the email link: verifies the token, then redirects to the
    frontend with ?verify=success|failed|expired|invalid so the SPA can show a message.
    """
    try:
        await confirm_email_verification(EmailVerificationConfirm(token=token), db)
        return RedirectResponse(
            url=_frontend_verify_url(verify="success"),
            status_code=status.HTTP_302_FOUND,
        )
    except HTTPException as exc:
        code = "failed"
        detail = str(exc.detail).lower() if exc.detail else ""
        if "expired" in detail:
            code = "expired"
        elif "invalid" in detail:
            code = "invalid"
        logger.info("verify_email_click: redirect with verify=%s (http %s)", code, exc.status_code)
        return RedirectResponse(
            url=_frontend_verify_url(verify=code),
            status_code=status.HTTP_302_FOUND,
        )
    except Exception:
        logger.exception("verify_email_click: unexpected error")
        return RedirectResponse(
            url=_frontend_verify_url(verify="failed"),
            status_code=status.HTTP_302_FOUND,
        )
