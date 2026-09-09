# Changelog

Notable approved repository changes are recorded here. This is not a task backlog.

## Unreleased

- No pending changes.

## 2026-09-09 - P004: Finalize authentication foundation

### Added

- Migration `b71f4e9c2a10`, email/password and mobile-OTP authentication, activation/verification, recovery, account states, session/logout behavior, Remember Me, failed-login protection, platform-admin authentication, and authenticated company listing.
- Development notification-provider abstraction with hashed password, OTP, session, and token persistence; no production delivery provider.

### Validated

- Docker/PostgreSQL, Alembic at `b71f4e9c2a10`, `/health`, `/health/database`, 18 backend tests including 10 authentication tests, frontend production build, and secret-leakage review.
- Migration batch-operation compatibility for SQLite upgrade/downgrade tests.

## 2026-09-08 - P003: Complete database foundation

### Added

- PostgreSQL 16 Docker development environment, SQLAlchemy 2.x, Alembic, and migration `58d8a59c599f`.
- Identity, authentication-method, company, user-company-access, branch, warehouse, and RBAC database foundations.
- Database health endpoint, P003 automated tests, and developer documentation.

### Validated

- Live PostgreSQL migration and table verification.
- Backend health and database-connectivity endpoints, complete backend test suite, and frontend production build.
- Published checkpoint: `7bbbd3eb2f57f2105879c1a6c185b6b7f940a354` on `origin/main`.
