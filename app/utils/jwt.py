from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import jwt

from app.core.config import settings


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if isinstance(to_encode.get("user_id"), UUID):
        to_encode["user_id"] = str(to_encode["user_id"])

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": "access",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc

    user_id = payload.get("user_id")
    if user_id is None:
        raise ValueError("Invalid token payload")

    try:
        payload["user_id"] = UUID(str(user_id))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid token payload") from exc

    if payload.get("token_type") not in (None, "access"):
        raise ValueError("Invalid token type")

    return payload
