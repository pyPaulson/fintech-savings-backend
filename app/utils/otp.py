from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from app.core.config import settings


def generate_otp(length: int = 6) -> str:
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(*, purpose: str, email: str, otp: str) -> str:
    payload = f"{purpose}:{email.strip().lower()}:{otp}".encode("utf-8")
    secret = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(secret, payload, sha256).hexdigest()


def verify_otp(*, purpose: str, email: str, otp: str, otp_hash: str | None) -> bool:
    if not otp_hash:
        return False
    expected_hash = hash_otp(purpose=purpose, email=email, otp=otp)
    return hmac.compare_digest(expected_hash, otp_hash)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def expires_in_minutes(minutes: int) -> datetime:
    return utc_now() + timedelta(minutes=minutes)
