# Fintech Savings Backend

FastAPI + PostgreSQL backend for a savings/transactions platform. It provides user management, authentication (email/password + Google OAuth), accounts, and transactions with admin controls and basic rate limiting.

## Stack
- Python 3.13, FastAPI, Pydantic v2
- Async SQLAlchemy + asyncpg
- Alembic for migrations
- JWT auth (access tokens in cookies or `Authorization: Bearer`)
- In-process sliding-window rate limiter for login attempts

## Project Layout
- `app/main.py` – FastAPI app wiring
- `app/routes/` – HTTP routes (auth, users, accounts, transactions)
- `app/controllers/` – request/business logic per domain
- `app/services/` – lower-level services (e.g., transaction_service)
- `app/models/` – SQLAlchemy models and enums
- `app/schemas/` – Pydantic request/response models
- `app/database/session.py` – async DB engine/session
- `migrations/` – Alembic migrations

## Prerequisites
- Python 3.13
- PostgreSQL reachable at the host/port you configure
- `pip install --upgrade pip` recommended

## Environment Variables (`.env`)
Populate a `.env` file in the repo root:

```
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
GOOGLE_CLIENT_ID=...           # optional, only if using Google OAuth
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
RATE_LIMIT_LOGIN_ATTEMPTS=5    # optional override
RATE_LIMIT_LOGIN_WINDOW_SECONDS=300
```

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head  # creates tables
```

## Running the API
```bash
uvicorn app.main:app --reload
```
App runs on http://localhost:8000 with Swagger UI at http://localhost:8000/docs.

## Authentication
- Login sets `access_token` HTTP-only cookie; you can also send `Authorization: Bearer <token>`.
- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`.
- First admin can be created without auth; subsequent admin creation requires an existing admin token.
- Rate limiting: `/auth/login` allows `RATE_LIMIT_LOGIN_ATTEMPTS` per `RATE_LIMIT_LOGIN_WINDOW_SECONDS` per client IP; exceeding returns 429 with `Retry-After` header.

## Key Endpoints (summary)
`[POST] /auth/login` — email/password login (rate limited)
`[POST] /auth/forgot-password` — issue reset token (dev returns token)
`[POST] /auth/reset-password` — reset password with token
`[POST] /auth/request-email-verification` — issue verification token
`[POST] /auth/verify-email` — confirm email
`[GET] /auth/me` — current user
`[GET] /auth/google/login` and `/auth/google/callback` — Google OAuth flow
`[POST] /auth/logout` — clear auth cookie

`[POST] /users/register` — register user
`[GET] /users/me` — current user profile
`[PATCH] /users/me` — update profile
`[DELETE] /users/me` — deactivate self
`[GET] /users/admin/` — list all users (admin)
`[POST] /users/admin/register` — create admin (open for first admin)
`[PATCH] /users/admin/me` — update current admin
`[GET|PATCH|DELETE] /users/admin/{user_id}` — admin read/update/deactivate user

`[GET] /accounts/` — list own accounts
`[GET] /accounts/{account_id}` — get account (self or admin)

`[POST] /transactions/` — create transaction (user/admin)
`[GET] /transactions/` — list own transactions
`[POST] /transactions/{reference}/complete` — mark complete (admin)
`[POST] /transactions/{reference}/fail` — mark failed (admin)

## Sample Usage
```bash
# Register a user
curl -X POST http://localhost:8000/users/register \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","password":"P@ssw0rd!"}'

# Login (cookie set in response)
curl -i -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ada@example.com","password":"P@ssw0rd!"}'

# Authenticated request using Bearer token
curl -H 'Authorization: Bearer <token>' http://localhost:8000/users/me
```

## Migrations
- Create migration: `alembic revision --autogenerate -m "message"`
- Apply latest: `alembic upgrade head`

## Testing
- Placeholder `tests/` directory exists; add `pytest`-style async tests using `httpx.AsyncClient` and a test database.

## Troubleshooting
- 429 on login: wait for `Retry-After` seconds or raise limits in `.env`.
- DB connection errors: verify `POSTGRES_*` values and that PostgreSQL is reachable.
- Missing Google creds: remove/ignore Google routes or supply valid OAuth values.

