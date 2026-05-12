# Secure Auth System

A portfolio-grade authentication backend built by Samuel Borba Cordeiro using FastAPI and SQLAlchemy to explore secure token lifecycle management, session control, brute-force mitigation, and service-oriented backend architecture.

This project was designed to go beyond a basic JWT tutorial or CRUD API. The main goal was to study how modern authentication systems handle trust, session persistence, token revocation, and repeated abuse while keeping the architecture modular and maintainable.

---

## Why this project exists

I wanted to build something that felt closer to a real backend system instead of a simple authentication demo.

While studying backend development and security concepts, I became interested in questions like:

- How are sessions managed securely?
- How do refresh tokens work internally?
- Why do modern systems rotate refresh tokens?
- How can compromised sessions be revoked?
- How do APIs defend against brute-force attacks?

This project became a way to explore those ideas through implementation.

---

## Main concepts explored

- JWT authentication
- rotating refresh token architecture
- stateless access vs stateful revocation
- session lifecycle management
- layered backend architecture
- brute-force mitigation
- audit logging
- request tracing
- security-oriented middleware

---

## Features

### Authentication
- user registration with Argon2 password hashing
- login using email or username
- short-lived access tokens
- rotating refresh tokens
- refresh token family tracking
- database-backed token revocation

### Session management
- active session listing
- per-session revocation
- logout from current session
- logout from all sessions

### Security
- rate limiting for repeated login attempts
- login attempt logging
- audit logging
- request ID middleware
- security headers middleware

### Recovery flow
- password reset token generation
- password reset validation flow

---

## Architecture

```txt
app/
├── api/            # HTTP routes
├── services/       # business logic
├── repositories/   # database layer
├── models/         # SQLAlchemy models
├── schemas/        # request/response validation
├── core/           # security, tokens, middleware, config
└── db/             # database session management

The project follows a layered architecture to separate:

transport logic
business rules
persistence
infrastructure concerns

This keeps the authentication flows easier to maintain and extend.

Threat model summary

This project attempts to reduce the impact of:

brute-force login attempts
credential stuffing
stolen refresh token replay
long-lived compromised sessions
stale authentication persistence

The refresh token system uses rotation and server-side revocation tracking to improve session control.

Tech stack
FastAPI
SQLAlchemy
PostgreSQL
Redis
Alembic
Pydantic
JWT (python-jose)
Argon2 (passlib)
Docker
Pytest
Run locally
python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

uvicorn app.main:app --reload
Example routes
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all

GET  /api/v1/users/me
GET  /api/v1/sessions
GET  /api/v1/health
Testing
pytest
Notes
The current rate limiter includes an in-memory fallback to keep the project self-contained and easy to review locally.
The password reset flow intentionally exposes reset tokens during development/demo usage. In production, tokens would only be delivered through email.
