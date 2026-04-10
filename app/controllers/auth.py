from __future__ import annotations

"""
Auth controller aggregator: keeps public import surface stable while grouping
session, password, and email verification flows into dedicated modules.
"""

from app.controllers.auth_session import get_current_user, login_user
from app.controllers.auth_password import request_password_reset, reset_password
from app.controllers.auth_verification import (
    confirm_email_verification,
    request_email_verification,
)

__all__ = [
    "get_current_user",
    "login_user",
    "request_password_reset",
    "reset_password",
    "confirm_email_verification",
    "request_email_verification",
]
