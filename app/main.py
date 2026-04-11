import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.routes import admin, user, auth, account, transaction, goal
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("app").setLevel(logging.INFO)
    if settings.EMAIL_ENABLED:
        logger.warning(
            "Transactional email enabled (Resend). Test mode (no domain): keep "
            "EMAIL_FROM using onboarding@resend.dev and register / verify using the "
            "same email you use to log into resend.com; other addresses will not receive mail. "
            "Logs: 'Resend accepted email' (ok) vs 'Resend API error' (rejected)."
        )
    yield


app = FastAPI(title="Fintech Savings API", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(user.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(transaction.router)
app.include_router(goal.router)


@app.get("/")
async def root():
    return {"message": "Backend is running!"}
