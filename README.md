# GrowFund Backend

FastAPI backend for `GrowFund`, a savings-first fintech product with room for investments later.

The current product logic is centered on:

- default `Flexi` and `Emergency` accounts created for every new user
- user-created goal accounts
- optional locked saving behavior for stronger discipline
- OTP-based email verification and password reset
- transactional email through Brevo

## Product Logic

When a user registers:

- a `Flexi` account is created automatically
- an `Emergency` account is created automatically

After that, the user can:

- create one or more goal accounts
- choose whether a goal should remain flexible or be treated like locked savings in the UI/product flow
- fund a goal directly
- optionally route part of a goal deposit into `Emergency`
  the intended product rule is up to `30%`
- withdraw from `Emergency` once per month

Investment is planned as a later extension. The current backend is savings-focused.

## Stack

- Python `3.13`
- FastAPI
- SQLAlchemy async
- PostgreSQL
- Alembic
- Pydantic v2
- JWT auth
- Jinja2 email templates
- Brevo transactional email

## Main Areas

- [app/main.py](/Users/paul/Desktop/Web_Learn/Projects/fintech-savings-backend/app/main.py:1): app setup, CORS, session middleware
- `app/routes/`: API routes
- `app/controllers/`: request handling
- `app/services/`: domain services
- `app/models/`: database models and enums
- `app/schemas/`: request and response schemas
- `app/templates/`: transactional email templates
- `migrations/`: Alembic migrations

## Auth Features

Implemented auth flows:

- register with email/password
- login with JWT bearer token
- OTP email verification
- forgot password with email OTP
- reset password with OTP + new password
- success emails after verification and password reset

There is backend support for Google token login, but the frontend Google flow is intentionally paused right now because the current frontend testing is happening in Expo Go.

## Key Routes

Auth:

- `POST /users/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/request-email-verification`
- `POST /auth/verify-email`
- `POST /auth/forgot-password`
- `POST /auth/verify-reset-otp`
- `POST /auth/reset-password`
- `POST /auth/google/mobile`

Savings data:

- `GET /accounts`
- `GET /accounts/{account_id}`
- `GET /transactions`
- `POST /transactions`
- `GET /goals`
- `POST /goals`
- `GET /goals/{goal_id}`
- `PATCH /goals/{goal_id}`
- `POST /goals/{goal_id}/deposit`

Use `/docs` for the live OpenAPI reference.

## Environment Variables

Create `.env` in the project root.

```env
# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email / Brevo
EMAIL_ENABLED=true
BREVO_API_KEY=
EMAIL_FROM=GrowFund <noreply@yourdomain.com>
FRONTEND_BASE_URL=http://localhost:8081
BACKEND_CORS_ORIGINS=http://localhost:8081,http://127.0.0.1:8081
EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES=10
PASSWORD_RESET_OTP_EXPIRE_MINUTES=10
OTP_RESEND_COOLDOWN_SECONDS=60

# Google (optional for now)
GOOGLE_CLIENT_ID=
GOOGLE_WEB_CLIENT_ID=
GOOGLE_IOS_CLIENT_ID=
GOOGLE_ANDROID_CLIENT_ID=
GOOGLE_EXPO_CLIENT_ID=
```

Notes:

- `EMAIL_FROM` must be a verified sender in Brevo.
- On a real phone, the frontend should call your machine using your LAN IP, not `127.0.0.1`.
- If you are not testing email locally, set `EMAIL_ENABLED=false`.

## Run Locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend base URL:

- `http://127.0.0.1:8000`

Docs:

- `http://127.0.0.1:8000/docs`

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Email Templates

Current templates live in `app/templates/` and include:

- email verification OTP
- password reset OTP
- email verified success
- password reset success

They are styled to match the GrowFund product direction.

## Troubleshooting

- No email arrives:
  check Brevo sender verification, API key, and backend logs.
- OTP not stored:
  confirm the user actually exists before requesting verification/reset flows.
- Backend fails on startup:
  reinstall dependencies with `pip install -r requirements.txt`.
- Mobile app cannot connect:
  use your machine's LAN IP in the frontend env.

## Status

This backend is in a good place for savings flows, auth, and dashboard data.

The next major product area is investment logic:

- deciding how locked savings transitions into investable balances
- defining risk buckets or products
- building transfer rules between savings and investments
