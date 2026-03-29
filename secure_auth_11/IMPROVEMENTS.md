# Improvements Implemented

## Critical fixes
- Added global exception handling with standardized error payloads in `app/core/exception_handlers.py`.
- Invalid tokens now return HTTP 401 with `error=invalid_token` instead of bubbling into 500 responses.
- Added logout ownership checks so a user cannot revoke another user's refresh token.
- Refactored session modeling: sessions now represent stable devices and refresh rotation updates the same session instead of creating a new one.
- Removed database creation from application startup; tests now use isolated databases and the versioned SQLite file was removed.
- Added Alembic support with an initial migration.

## Important improvements
- Replaced in-memory rate limiting with a Redis-backed implementation with an in-memory fallback for local testing.
- Added `iss`, `aud`, `iat`, and `nbf` JWT claims and separate secrets for access, refresh, and password reset tokens.
- Added `device_id` support and `last_seen_at` updates on authenticated requests.
- Improved docker stack to include PostgreSQL and Redis with healthchecks.
- Added 20+ tests with isolated database setup via `tests/conftest.py`.
- Added structured request logging and request IDs.

## Still possible in future
- MFA / TOTP with recovery codes.
- Refresh token reuse detection across token families.
- Prometheus / Grafana observability stack.
- GitHub Actions CI pipeline.
- Background cleanup jobs and retention policies.
