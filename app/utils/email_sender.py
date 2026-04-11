from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailSendError(Exception):
    """Outbound email could not be sent via Resend."""


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

    key = (settings.RESEND_API_KEY or "").strip()
    if not key:
        logger.error("RESEND_API_KEY is empty; cannot send email to %s", to)
        raise EmailSendError("RESEND_API_KEY is not configured")

    payload: dict[str, Any] = {
        "from": settings.EMAIL_FROM.strip(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    timeout = httpx.Timeout(settings.EMAIL_REQUEST_TIMEOUT_SECONDS)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.RequestError as exc:
        logger.exception("Resend HTTP request failed for recipient=%s", to)
        raise EmailSendError("Could not reach Resend API") from exc

    if response.is_success:
        resend_id: str | None = None
        try:
            data = response.json()
            if isinstance(data, dict):
                rid = data.get("id")
                resend_id = str(rid) if rid is not None else None
        except ValueError:
            pass
        logger.info(
            "Resend accepted email: id=%s recipient=%s subject=%r",
            resend_id,
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
        "Resend API error: status=%s recipient=%s detail=%s body=%s",
        response.status_code,
        to,
        detail,
        body,
    )
    raise EmailSendError(f"Resend returned HTTP {response.status_code}")
