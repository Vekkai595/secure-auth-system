# Secure Auth System

A backend authentication system I built with **FastAPI**, **SQLAlchemy**, **JWT**, **Argon2**, **PostgreSQL**, **Redis**, **Alembic**, **Docker** and **Pytest** to study how more serious login systems work behind the scenes.

The idea of this project was not to build just a simple “login with JWT” API. I wanted to create something closer to a real backend, with sessions, rotating refresh tokens, token revocation, login abuse protection, audit logs, password reset and a layered architecture.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688?logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-0.35.0-499848)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.43-D71F00?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![psycopg](https://img.shields.io/badge/psycopg-3.2.9-4169E1)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-1.13.2-blue)
![Pydantic](https://img.shields.io/badge/Pydantic-2.11.7-E92063?logo=pydantic&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-python--jose-000000?logo=jsonwebtokens&logoColor=white)
![Argon2](https://img.shields.io/badge/Passwords-Argon2-purple)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-8.4.1-0A9EDC?logo=pytest&logoColor=white)
![HTTPX](https://img.shields.io/badge/HTTPX-0.28.1-blue)
![API](https://img.shields.io/badge/API-REST-black)
![Architecture](https://img.shields.io/badge/architecture-layered-orange)
![License](https://img.shields.io/badge/license-not%20defined-lightgrey)

---

## Overview

I created **Secure Auth System** to understand authentication in a deeper way.

In many projects, authentication becomes just a login route that returns a token. Here, I wanted to go further: I wanted to understand how a backend handles sessions, expiring tokens, refresh tokens, real logout, revocation, multiple devices, repeated login attempts and password reset.

The project is a REST API organized in layers, with routes, services, repositories, models, schemas and centralized configuration. This makes the code easier to understand, maintain and expand.

---

## Why I Built This Project

I wanted to build something that felt closer to a real backend system, not just a tutorial demo.

While studying backend development and security, I started asking questions like:

- How does a system know which sessions are active?
- How does a refresh token actually work behind the scenes?
- Why should refresh tokens be rotated?
- How can I revoke one specific session?
- How can I log out from all devices?
- How can I reduce abuse from repeated login attempts?
- How should important security events be logged?
- How can this kind of system stay organized instead of becoming messy?

This project was my way of answering those questions by building something real.

---

## What the System Does

The system can create users, authenticate them, generate tokens, refresh tokens, list sessions, revoke sessions, change passwords, reset passwords and log important security events.

It also has a stronger security foundation than a basic login system because it uses Argon2 password hashing, short-lived access tokens, rotating refresh tokens and database-controlled sessions.

---

## Main Features

### Authentication

- User registration.
- Login with email or username.
- Passwords hashed with Argon2.
- Short-lived JWT access token.
- Long-lived JWT refresh token.
- Rotating refresh tokens.
- Session identification through `sid` inside the token.
- Separation between access tokens, refresh tokens and password reset tokens.

### Sessions

- Session creation per device.
- Device identification through `X-Device-ID`.
- Automatic device ID fallback using IP and user-agent.
- Listing active and past sessions.
- `last_seen_at` updates on authenticated requests.
- Revocation of one specific session.
- Logout from the current session.
- Logout from all sessions.

### Security

- Password hashing with Argon2.
- Refresh tokens stored in the database to allow revocation.
- Refresh token rotation on every refresh.
- `jti` tracking for refresh tokens.
- Token family tracking with `token_family`.
- Login rate limiting.
- Rate limiting by IP and identifier.
- In-memory fallback if Redis is unavailable.
- Login attempt logs.
- Audit logs.
- Request ID middleware.
- Basic security headers.
- Standardized error handling.

### Password Reset

- Password reset token generation.
- Reset token stored as a hash in the database.
- Validation for expired or already used reset tokens.
- Refresh token revocation after password reset.
- Session revocation after password reset.

### Quality

- Automated tests with Pytest.
- Tests for registration, login, refresh, logout, sessions, rate limiting and password reset.
- Initial database migration with Alembic.
- Dockerfile for the API.
- Docker Compose with PostgreSQL, Redis and the API.

---

## Main Routes

```txt
GET    /api/v1/health

POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/logout-all
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password

GET    /api/v1/users/me
PATCH  /api/v1/users/me
PATCH  /api/v1/users/me/password

GET    /api/v1/sessions
DELETE /api/v1/sessions/{session_id}
```

---

## How the Authentication Flow Works

### 1. Registration

The user creates an account with an email, username and password.

The password is not stored as plain text. I use Argon2 to generate a password hash and only store that hash in the database.

### 2. Login

On login, the user can authenticate with either email or username.

If the password is correct, the system creates a session and returns two tokens:

- `access_token`: used to access protected routes;
- `refresh_token`: used to generate a new pair of tokens when the access token expires.

### 3. Access Token

The access token is short-lived and stateless. It carries information such as:

- user (`sub`);
- token type;
- session (`sid`);
- expiration;
- issuer;
- audience.

### 4. Refresh Token

The refresh token is also a JWT, but it is controlled in the database through its `jti`.

When the user refreshes tokens, the old refresh token is revoked and a new one is created. This prevents the same refresh token from being reused forever.

### 5. Sessions

Each session stores information such as:

- user;
- device ID;
- current refresh token;
- IP address;
- user-agent;
- creation time;
- last seen time;
- revocation time.

This allows the system to list sessions and revoke specific sessions.

### 6. Logout

On logout, the refresh token is revoked and the related session is also marked as revoked.

On logout-all, all user sessions and all user refresh tokens are revoked.

---

## Project Architecture

I organized the project into layers to separate responsibilities.

```txt
app/
├── api/            HTTP routes and API dependencies
├── services/       business logic
├── repositories/   database access
├── models/         SQLAlchemy models
├── schemas/        input and output validation with Pydantic
├── core/           tokens, security, config, middleware and errors
└── db/             database session and base

alembic/             database migrations
tests/               automated tests
```

The idea is to avoid putting all the logic inside the routes. Routes receive the request, services apply the business logic and repositories communicate with the database.

---

## Detailed Project Structure

```txt
secure-auth-system/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── health.py
│   │           ├── sessions.py
│   │           └── users.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exception_handlers.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   ├── rate_limit.py
│   │   ├── security.py
│   │   └── tokens.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── audit_log.py
│   │   ├── login_attempt.py
│   │   ├── password_reset.py
│   │   ├── refresh_token.py
│   │   ├── session.py
│   │   └── user.py
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── alembic/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## Tech Stack

### Backend

- Python 3.12
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings

### Database and Persistence

- SQLAlchemy
- PostgreSQL
- psycopg
- Alembic

### Security and Authentication

- JWT with `python-jose`
- Argon2 with `passlib[argon2]`
- Refresh token rotation
- Token revocation
- Session tracking
- Login rate limiting

### Infrastructure

- Docker
- Docker Compose
- Redis

### Tests

- Pytest
- HTTPX
- FastAPI TestClient

---

## How to Run With Docker

This is the most complete option because it starts the API, PostgreSQL and Redis together.

```bash
docker compose up --build
```

The API will be available at:

```txt
http://localhost:8000
```

FastAPI's automatic documentation will be available at:

```txt
http://localhost:8000/docs
```

---

## How to Run Locally Without Docker

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

On Linux/macOS:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment file:

```bash
cp .env.example .env
```

Then run the API:

```bash
uvicorn app.main:app --reload
```

---

## Environment Variables

Example based on `.env.example`:

```txt
APP_NAME=Secure Auth System
ENVIRONMENT=development
DEBUG=false
ACCESS_TOKEN_SECRET_KEY=change-me-access-secret-in-production
REFRESH_TOKEN_SECRET_KEY=change-me-refresh-secret-in-production
PASSWORD_RESET_SECRET_KEY=change-me-reset-secret-in-production
ALGORITHM=HS256
TOKEN_ISSUER=secure-auth-system
TOKEN_AUDIENCE=secure-auth-api
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
PASSWORD_RESET_EXPIRE_MINUTES=20
DATABASE_URL=postgresql+psycopg://secure_auth:secure_auth@postgres:5432/secure_auth
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
LOGIN_RATE_LIMIT_MAX_ATTEMPTS=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=300
```

In production, `ACCESS_TOKEN_SECRET_KEY`, `REFRESH_TOKEN_SECRET_KEY` and `PASSWORD_RESET_SECRET_KEY` must be replaced with strong private secrets.

---

## Database

The project includes an initial Alembic migration.

It creates tables for:

- users;
- sessions;
- refresh tokens;
- login attempts;
- audit logs;
- password reset tokens.

To run the migrations:

```bash
alembic upgrade head
```

---

## Tests

To run the tests:

```bash
pytest
```

The tests cover important parts of the system, including:

- health check;
- registration;
- duplicate email;
- duplicate username;
- invalid username;
- login with email;
- login with username;
- invalid password;
- rate limit after multiple failed attempts;
- `/users/me` route;
- invalid token;
- refresh token;
- invalid refresh token;
- expired refresh token;
- logout;
- logout with another user's token;
- logout from all sessions;
- session listing;
- session revocation;
- trying to revoke another user's session;
- `last_seen_at` update;
- multiple devices;
- password reset;
- invalid reset token;
- expired reset token;
- request ID on errors.

---

## Quick Usage Examples

### Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user1",
    "password": "StrongPassword123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: device-a" \
  -d '{
    "identifier": "user@example.com",
    "password": "StrongPassword123"
  }'
```

### Access the Current User

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: device-a" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### List Sessions

```bash
curl http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Revoke a Session

```bash
curl -X DELETE http://localhost:8000/api/v1/sessions/1 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## What I Wanted to Study With This Project

This project helped me practice concepts that appear in real systems, such as:

- the difference between access tokens and refresh tokens;
- why refresh tokens need server-side control;
- how to revoke sessions in a JWT-based system;
- why logout with pure JWT is not that simple;
- how to reduce the risk of old tokens still working;
- how to log sensitive security events;
- how to separate business logic from HTTP routes;
- how to test authentication flows.

---

## Project Limits

This project is a study and portfolio base. It already has several security ideas, but it should not be treated as production-ready without professional review.

Some important points:

- It has no frontend.
- It does not send real emails in the password reset flow.
- The reset token is generated by the backend, but email delivery is not implemented.
- It does not have real email verification.
- It does not have 2FA.
- The rate limiter has an in-memory fallback to make local testing easier.
- Production configuration needs strong secrets.
- Deployment, observability, backups, monitoring and hardening would need review before real usage.

---

## Things I Did Not Want to Fake

I did not want to put things in the README that the project does not actually do.

So, to be clear:

- it is not a complete enterprise authentication system;
- it does not have an admin dashboard;
- it does not send real emails;
- it does not have Google/GitHub OAuth;
- it does not have multi-factor authentication;
- it does not have a frontend;
- it is not a ready-to-install library for any app;
- it is not an authentication SaaS.

The focus here was backend architecture and authentication flow security.

---

## Possible Future Improvements

Some things I could add later:

- real email delivery for password reset;
- email verification;
- two-factor authentication;
- OAuth with Google or GitHub;
- a dashboard to view sessions and logs;
- more aggressive refresh token reuse detection;
- basic load tests;
- more detailed OpenAPI documentation;
- CI workflow with GitHub Actions;
- cloud deployment;
- more complete structured logs;
- metrics with Prometheus or another monitoring system;
- more complete roles and permissions.

---

## Why This Project Matters

Authentication looks simple when we only see a login screen, but behind it there are many important decisions.

A system needs to decide how long tokens last, how access is renewed, how logout works, how abuse is detected, how sessions are revoked and how sensitive information is protected.

I built **Secure Auth System** to study exactly this invisible part behind many real applications.

---

## Author

**Samuel Borba Cordeiro**

Student developer from Brazil focused on backend, security, authentication systems, API architecture and real-world impact projects.

---

## License Note

This repository does not have a defined license yet.

If it becomes open source in the future, the best option is to add a real `LICENSE` file and update the license badge at the top of this README.
