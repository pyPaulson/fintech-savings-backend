from __future__ import annotations

from app.core.config import settings
from app.utils.email_sender import send_email
from app.utils.email_templates import render_template


async def send_verification_email(*, to_email: str, recipient_name: str, otp: str) -> None:
    display_name = (recipient_name or "").strip() or "there"
    html = render_template(
        "verify_email.html",
        app_name=settings.APP_NAME,
        name=display_name,
        otp=otp,
        expiry_minutes=settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES,
    )
    subject = f"Verify your email — {settings.APP_NAME}"
    await send_email(to_email, subject, html)


async def send_password_reset_email(*, to_email: str, recipient_name: str, otp: str) -> None:
    display_name = (recipient_name or "").strip() or "there"
    html = render_template(
        "password_reset.html",
        app_name=settings.APP_NAME,
        name=display_name,
        otp=otp,
        expiry_minutes=settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES,
    )
    subject = f"Reset your password — {settings.APP_NAME}"
    await send_email(to_email, subject, html)


async def send_email_verified_success_email(*, to_email: str, recipient_name: str) -> None:
    display_name = (recipient_name or "").strip() or "there"
    html = render_template(
        "email_verified_success.html",
        app_name=settings.APP_NAME,
        name=display_name,
    )
    subject = f"Your email is verified — {settings.APP_NAME}"
    await send_email(to_email, subject, html)


async def send_password_reset_success_email(*, to_email: str, recipient_name: str) -> None:
    display_name = (recipient_name or "").strip() or "there"
    html = render_template(
        "password_reset_success.html",
        app_name=settings.APP_NAME,
        name=display_name,
    )
    subject = f"Your password was changed — {settings.APP_NAME}"
    await send_email(to_email, subject, html)
