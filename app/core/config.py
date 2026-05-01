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
    GOOGLE_IOS_CLIENT_ID: str = ""
    GOOGLE_ANDROID_CLIENT_ID: str = ""
    GOOGLE_WEB_CLIENT_ID: str = ""
    GOOGLE_EXPO_CLIENT_ID: str = ""

    # Rate limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300

    # Product / email
    APP_NAME: str = "GrowFund"

    # Brevo transactional email
    EMAIL_ENABLED: bool = True
    BREVO_API_KEY: str = ""
    EMAIL_FROM: str = "GrowFund <noreply@yourdomain.com>"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    EMAIL_REQUEST_TIMEOUT_SECONDS: float = 20.0
    EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES: int = 10
    PASSWORD_RESET_OTP_EXPIRE_MINUTES: int = 10
    OTP_RESEND_COOLDOWN_SECONDS: int = 60

    # App clients
    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:8081,"
        "http://127.0.0.1:8081"
    )

    class Config:
        env_file = ".env"

    @property
    def cors_origins(self) -> list[str]:
        raw = (self.BACKEND_CORS_ORIGINS or "").strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def google_allowed_client_ids(self) -> set[str]:
        return {
            value.strip()
            for value in {
                self.GOOGLE_CLIENT_ID,
                self.GOOGLE_IOS_CLIENT_ID,
                self.GOOGLE_ANDROID_CLIENT_ID,
                self.GOOGLE_WEB_CLIENT_ID,
                self.GOOGLE_EXPO_CLIENT_ID,
            }
            if value and value.strip()
        }

    @model_validator(mode="after")
    def _email_config_consistent(self) -> "Settings":
        if self.EMAIL_ENABLED and not (self.BREVO_API_KEY or "").strip():
            raise ValueError("BREVO_API_KEY is required when EMAIL_ENABLED is true")
        return self


settings = Settings()
