# Changelog

Notable approved repository changes are recorded here. This is not a task backlog.

## Unreleased

- Documentation checkpoint pending review; no implementation work is included.

## 2026-09-08 - P003: Complete database foundation

### Added

- PostgreSQL 16 Docker development environment, SQLAlchemy 2.x, Alembic, and migration `58d8a59c599f`.
- Identity, authentication-method, company, user-company-access, branch, warehouse, and RBAC database foundations.
- Database health endpoint, P003 automated tests, and developer documentation.

### Validated

- Live PostgreSQL migration and table verification.
- Backend health and database-connectivity endpoints, complete backend test suite, and frontend production build.
- Published checkpoint: `7bbbd3eb2f57f2105879c1a6c185b6b7f940a354` on `origin/main`.
