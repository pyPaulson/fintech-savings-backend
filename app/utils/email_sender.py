from __future__ import annotations

import logging
from email.utils import parseaddr
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailSendError(Exception):
    """Outbound email could not be sent via Brevo."""


def _parse_sender(raw_sender: str) -> dict[str, str]:
    name, email = parseaddr(raw_sender.strip())
    if not email:
        raise EmailSendError("EMAIL_FROM must contain a valid sender email")
    sender = {"email": email}
    if name:
        sender["name"] = name
    return sender


async def send_email(
    to: str,
    subject: str,
    html: str,
    *,
    reply_to: str | None = None,
) -> None:
    if not settings.EMAIL_ENABLED:
        logger.debug("Email disabled; skipping outbound message to %s", to)
        return

    key = (settings.BREVO_API_KEY or "").strip()
    if not key:
        logger.error("BREVO_API_KEY is empty; cannot send email to %s", to)
        raise EmailSendError("BREVO_API_KEY is not configured")

    payload: dict[str, Any] = {
        "sender": _parse_sender(settings.EMAIL_FROM),
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
    }
    if reply_to:
        _, reply_email = parseaddr(reply_to.strip())
        if reply_email:
            payload["replyTo"] = {"email": reply_email}

    timeout = httpx.Timeout(settings.EMAIL_REQUEST_TIMEOUT_SECONDS)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                BREVO_API_URL,
                headers={
                    "accept": "application/json",
                    "api-key": key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.RequestError as exc:
        logger.exception("Brevo HTTP request failed for recipient=%s", to)
        raise EmailSendError("Could not reach Brevo API") from exc

    if response.is_success:
        message_id: str | None = None
        try:
            data = response.json()
            if isinstance(data, dict):
                rid = data.get("messageId")
                message_id = str(rid) if rid is not None else None
        except ValueError:
            pass
        logger.info(
            "Brevo accepted email: message_id=%s recipient=%s subject=%r",
            message_id,
            to,
            subject[:80],
        )
        return

    try:
        body: Any = response.json()
    except ValueError:
        body = (response.text or "")[:500]

    detail = ""
    if isinstance(body, dict):
        detail = str(body.get("message") or body.get("error") or "")

    logger.error(
        "Brevo API error: status=%s recipient=%s detail=%s body=%s",
        response.status_code,
        to,
        detail,
        body,
    )
    raise EmailSendError(f"Brevo returned HTTP {response.status_code}")
