from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Rate limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300

    # Product / email
    APP_NAME: str = "Fintech Savings"

    # Resend (https://resend.com/docs) — no domain needed for testing:
    # Use onboarding@resend.dev in EMAIL_FROM; the app user's email must match your Resend login.
    EMAIL_ENABLED: bool = True
    RESEND_API_KEY: str = ""
    # Override in production with a verified domain, e.g. "Fintech Savings <noreply@yourdomain.com>"
    EMAIL_FROM: str = "Fintech Savings <onboarding@resend.dev>"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    # Public URL of this API (used in verification emails). Must be reachable from the user’s browser.
    PUBLIC_API_BASE_URL: str = "http://localhost:8000"
    EMAIL_VERIFICATION_PATH: str = "/verify-email"
    PASSWORD_RESET_PATH: str = "/reset-password"
    EMAIL_REQUEST_TIMEOUT_SECONDS: float = 20.0

    class Config:
        env_file = ".env"

    @model_validator(mode="after")
    def _email_config_consistent(self) -> "Settings":
        if self.EMAIL_ENABLED and not (self.RESEND_API_KEY or "").strip():
            raise ValueError("RESEND_API_KEY is required when EMAIL_ENABLED is true")
        return self


settings = Settings()
