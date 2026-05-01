from __future__ import annotations

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token

from app.core.config import settings


def verify_google_identity_token(token: str) -> dict:
    token = (token or "").strip()
    if not token:
        raise ValueError("Missing Google ID token")

    try:
        payload = google_id_token.verify_oauth2_token(token, GoogleRequest())
    except Exception as exc:
        raise ValueError("Invalid Google ID token") from exc

    allowed_client_ids = settings.google_allowed_client_ids
    if not allowed_client_ids:
        raise ValueError("Google client IDs are not configured")

    aud = str(payload.get("aud") or "").strip()
    if aud not in allowed_client_ids:
        raise ValueError("Google token audience is not allowed")

    if not payload.get("email_verified", False):
        raise ValueError("Google email is not verified")

    return payload
