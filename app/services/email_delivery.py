from __future__ import annotations

from urllib.parse import urlencode

from app.core.config import settings
from app.utils.email_sender import send_email
from app.utils.email_templates import render_template


def _frontend_action_url(path: str, token: str) -> str:
    base = settings.FRONTEND_BASE_URL.rstrip("/")
    segment = path.lstrip("/")
    return f"{base}/{segment}?{urlencode({'token': token})}"


def _backend_verify_click_url(token: str) -> str:
    """One-click link: browser hits API, which verifies then redirects to the frontend."""
    base = settings.PUBLIC_API_BASE_URL.rstrip("/")
    return f"{base}/auth/verify-email/click?{urlencode({'token': token})}"


async def send_verification_email(*, to_email: str, recipient_name: str, token: str) -> None:
    display_name = (recipient_name or "").strip() or "there"
    verify_url = _backend_verify_click_url(token)
    html = render_template(
        "verify_email.html",
        app_name=settings.APP_NAME,
        name=display_name,
        verify_url=verify_url,
    )
    subject = f"Confirm your email — {settings.APP_NAME}"
    await send_email(to_email, subject, html)


async def send_password_reset_email(*, to_email: str, recipient_name: str, token: str) -> None:
    display_name = (recipient_name or "").strip() or "there"
    reset_url = _frontend_action_url(settings.PASSWORD_RESET_PATH, token)
    html = render_template(
        "password_reset.html",
        app_name=settings.APP_NAME,
        name=display_name,
        reset_url=reset_url,
    )
    subject = f"Reset your password — {settings.APP_NAME}"
    await send_email(to_email, subject, html)
