from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.routes import user, auth, account, transaction
from app.core.config import settings

app = FastAPI(title="Fintech Savings API")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(transaction.router)


@app.get("/")
async def root():
    return {"message": "Backend is running!"}
