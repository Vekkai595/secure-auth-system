# Secure Auth System

A portfolio-grade authentication backend built with FastAPI and SQLAlchemy to demonstrate secure token lifecycle management, session tracking, brute-force mitigation, and clean service-oriented architecture.

## Why this project exists

I wanted a project that showed more than CRUD or a basic JWT tutorial. This system treats authentication as a computer science and security problem: how to model trust, rotate credentials safely, track sessions, revoke compromised tokens, and defend against repeated abuse.

## Main CS ideas

- token lifecycle design
- stateless access vs stateful revocation
- rate limiting as a bounded-time counting problem
- session modelling
- layered architecture and separation of concerns
- security trade-offs between simplicity and control

## Features

- user registration with Argon2 password hashing
- login by email or username
- short-lived access tokens
- rotating refresh tokens with database-backed revocation
- session listing and per-session revocation
- logout-all support
- password reset flow for demo and testing
- audit logging and login attempt logging
- request ID and security headers middleware

## Project structure

- `app/api/` HTTP layer only
- `app/services/` business logic
- `app/repositories/` database access
- `app/models/` SQLAlchemy models
- `app/core/` security, tokens, config, middleware
- `tests/` behavior checks

## Threat model summary

This project is designed to reduce the impact of:

- credential stuffing and brute force through rate limiting
- long-lived session abuse through rotating refresh tokens
- refresh token replay through server-side revocation tracking
- stale session persistence through logout and logout-all operations

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Example routes

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/logout-all`
- `GET /api/v1/users/me`
- `GET /api/v1/sessions`
- `GET /api/v1/health`

## Notes

- The current rate limiter uses an in-memory fallback to keep the project self-contained and easy to review. A Redis adapter can be plugged in later.
- The password reset route intentionally returns the token so the flow is easy to test in a portfolio/demo setting. In a production deployment, this would be sent through email only.

## Next upgrades

- Redis-backed distributed rate limiter
- MFA / TOTP
- email verification workflow
- admin reporting endpoints
- GitHub Actions for lint, tests, and security checks
