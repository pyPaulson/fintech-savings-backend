# Fintech Savings Backend

I’m Paulson. This repo is the API for a savings-style app: users, accounts (flexi, emergency, etc.), transactions, and auth that doesn’t feel bolted on. I built it with FastAPI and PostgreSQL, async end to end, because I didn’t want the boring stuff to get slow when traffic shows up.

## What’s in the stack

- Python 3.13, FastAPI, Pydantic v2  
- Async SQLAlchemy + asyncpg  
- Alembic for schema changes  
- JWTs (HTTP-only cookie or `Authorization: Bearer`)  
- Resend + Jinja2 templates for transactional email (verify email, password reset)  
- Google OAuth wired up if you fill the Google env vars  
- In-process rate limiting on login so password stuffing isn’t free

## How I organized the code

- `app/main.py` — app factory, lifespan, middleware  
- `app/routes/` — routers (auth, users, accounts, transactions, goals, admin)  
- `app/controllers/` — what each request actually does  
- `app/services/` — things like creating transactions and default accounts  
- `app/models/` — SQLAlchemy models and enums  
- `app/schemas/` — request/response shapes  
- `app/templates/` — HTML email templates  
- `app/database/session.py` — async engine and sessions  
- `migrations/` — Alembic

## Before you run anything

- Python 3.13  
- PostgreSQL running and reachable  
- I usually bump pip first: `pip install --upgrade pip`

## Environment variables

Put a `.env` in the project root. Here’s what I use (fill in your own secrets):

```env
# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT
SECRET_KEY=change-me-to-something-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Google OAuth (only if you use Google login)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Rate limits (optional; defaults are fine)
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW_SECONDS=300

# Email (Resend) — if EMAIL_ENABLED is true, RESEND_API_KEY is required
EMAIL_ENABLED=true
RESEND_API_KEY=re_...
EMAIL_FROM=Fintech Savings <onboarding@resend.dev>
FRONTEND_BASE_URL=http://localhost:3000
PUBLIC_API_BASE_URL=http://localhost:8000
```

A few notes from my own testing:

- With `onboarding@resend.dev`, Resend only delivers test mail to the address you used to sign up on resend.com — so register in the app with that same email, or verify a domain and change `EMAIL_FROM` for real sends.  
- `PUBLIC_API_BASE_URL` is the link the verification email uses (`/auth/verify-email/click`). It has to be a URL your browser can open (same host/port as your API).  
- If you’re not sending mail locally, set `EMAIL_ENABLED=false` and you can skip the Resend key.

## Run it locally

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000 — OpenAPI docs at `/docs`.

## Auth (how I set it up)

- Login sets an HTTP-only `access_token` cookie; Bearer tokens work too.  
- Expiry comes from `ACCESS_TOKEN_EXPIRE_MINUTES`.  
- After too many failed logins from the same IP you get `429` and a `Retry-After` header.  
- First admin bootstrap is handled in the admin routes; after that you need an admin token for admin stuff.

## Endpoints I actually use

**Auth**

- `POST /auth/login` — login (rate limited)  
- `POST /auth/logout` — clear cookie  
- `GET /auth/me` — current user  
- `POST /auth/forgot-password` — sends reset email (generic JSON response either way)  
- `POST /auth/reset-password` — body: `token`, `new_password`  
- `POST /auth/request-email-verification` — sends verification email again  
- `POST /auth/verify-email` — body: `token` (JSON)  
- `GET /auth/verify-email/click?token=...` — same as above, but meant for the link in the email; verifies then redirects to `FRONTEND_BASE_URL` with `?verify=success` or `?verify=failed` etc.  
- Google OAuth: `/auth/google/callback` and the login entry point from `auth_google` router

**Users**

- `POST /users/register`  
- `GET /users/me`, `PATCH /users/me`, `DELETE /users/me`  
- Admin user routes under `/users/admin/...` as in the code

**Accounts & transactions**

- `GET /accounts/` — list my accounts  
- `GET /accounts/{account_id}`  
- `POST /transactions/` — create  
- `GET /transactions/` — list mine  
- `POST /transactions/{reference}/complete` and `.../fail` — admin completion flows  

**Savings goals**

Each goal gets its own `goal` ledger account. You set the target amount, start and end dates (your horizon), how often you want to deposit (`daily` / `weekly` / `biweekly` / `monthly`), and how much you plan to put in each period. Deposits post immediately as completed `goal_deposit` transactions; when the balance hits the target, the goal flips to `completed`.

- `POST /goals/` — create a goal  
- `GET /goals/` — list yours (balance + progress %)  
- `GET /goals/{goal_id}` — detail  
- `PATCH /goals/{goal_id}` — rename or change status (`paused`, `cancelled`, etc.)  
- `POST /goals/{goal_id}/deposit` — body: `amount`, optional `description`

Exact paths are easiest to read from `/docs` — I’m not going to duplicate every admin route here.

## Quick curl examples

```bash
curl -X POST http://localhost:8000/users/register \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Paulson","last_name":"Dev","email":"you@example.com","password":"your-password-here"}'

curl -i -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"your-password-here"}'

curl -H 'Authorization: Bearer <paste-token>' http://localhost:8000/users/me
```

## Migrations

```bash
alembic revision --autogenerate -m "describe what changed"
alembic upgrade head
```

## When something breaks

- **429 on login** — wait or relax the rate limit env vars.  
- **DB errors** — check `POSTGRES_*` and that Postgres is up.  
- **No email** — check Resend dashboard logs; confirm `PUBLIC_API_BASE_URL` matches where uvicorn listens; watch server logs for `Resend accepted email` vs `Resend API error`.  
- **Google OAuth** — invalid or missing keys will show up when you hit those routes; fix the env or leave Google unused.

## Tests

There’s room for `pytest` + `httpx.AsyncClient` against a throwaway database when I get around to adding a proper test harness.

---

That’s the gist. If you’re reading this in the repo, you’re probably me or someone I handed the project to — either way, `/docs` is the source of truth for request bodies.
