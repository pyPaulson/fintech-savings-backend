from fastapi import FastAPI
from app.routes import user, auth

app = FastAPI(title="Fintech Savings API")

app.include_router(user.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Backend is running!"}
