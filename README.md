# Fintech Savings Backend (by Paulson)

I'm Paulson, and this is the backend I built for a savings + transactions platform. It runs on FastAPI with PostgreSQL, keeps auth tight (cookies or Bearer tokens), and ships rate limits so brute force logins bounce. I keep everything async because speed matters when money moves.

## Stack (my toolkit)
- Python 3.13, FastAPI, Pydantic v2
- Async SQLAlchemy + asyncpg
- Alembic for migrations
- JWT auth (cookie or `Authorization: Bearer`)
- Sliding-window login rate limiter (in-process)

## How I laid it out
- `app/main.py` – wires the app
- `app/routes/` – HTTP routes (auth, users, accounts, transactions)
- `app/controllers/` – request/business logic per domain
- `app/services/` – lower-level services (e.g., transaction_service)
- `app/models/` – SQLAlchemy models and enums
- `app/schemas/` – Pydantic request/response models
- `app/database/session.py` – async DB engine/session
- `migrations/` – Alembic migrations

## Before you start
- Python 3.13
- PostgreSQL at the host/port you configure
- `pip install --upgrade pip` (I always do this first)

## Environment (`.env`)
Drop a `.env` in the repo root:

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

## Spin it up (my flow)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head  # create tables
```

Run the API:
```bash
uvicorn app.main:app --reload
```
It serves http://localhost:8000 and Swagger UI at http://localhost:8000/docs.

## Auth rules (how I guard doors)
- Login sets an HTTP-only `access_token` cookie; Bearer tokens also work.
- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`.
- First admin can be created open; after that you need an admin token.
- Rate limit on `/auth/login`: `RATE_LIMIT_LOGIN_ATTEMPTS` per `RATE_LIMIT_LOGIN_WINDOW_SECONDS` per client IP. Exceeding returns 429 + `Retry-After`.

## Endpoints I reach for
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

## Sample calls (with me as the user)
```bash
# Register me
curl -X POST http://localhost:8000/users/register \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Paulson","last_name":"Developer","email":"paulson@example.com","password":"P@ssw0rd!"}'

# Login (cookie set in response)
curl -i -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"paulson@example.com","password":"P@ssw0rd!"}'

# Authenticated request using Bearer token
curl -H 'Authorization: Bearer <token>' http://localhost:8000/users/me
```

## Migrations
- Create: `alembic revision --autogenerate -m "message"`
- Apply latest: `alembic upgrade head`

## Testing
- `tests/` is ready for `pytest` async tests (use `httpx.AsyncClient` + a test DB).

## Troubleshooting (my quick checks)
- 429 on login: wait for `Retry-After` or bump limits in `.env`.
- DB connection errors: double-check `POSTGRES_*` and that PostgreSQL is reachable.
- No Google creds: drop the Google routes or set valid OAuth values.
