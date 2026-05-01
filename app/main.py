import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routes import admin, user, auth, account, transaction, goal
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger("app").setLevel(logging.INFO)
    if settings.EMAIL_ENABLED:
        logger.warning(
            "Transactional email enabled (Brevo). Make sure EMAIL_FROM is a sender "
            "you have verified inside Brevo and BREVO_API_KEY is set."
        )
    yield


app = FastAPI(title="Fintech Savings API", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

allow_origins = settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_credentials=allow_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(transaction.router)
app.include_router(goal.router)


@app.get("/")
async def root():
    return {"message": "Backend is running!"}
