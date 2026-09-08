# Next Steps

## Immediate Next Steps

1. Define account-provisioning workflows for Accline Services, including how it assigns the initial company Owner.
2. Implement secure authentication flows for email/password and mobile OTP using the existing `authentication_methods` structure; use a strong password hash and never persist OTP values.
3. Implement authenticated request handling that resolves a user and requires an active company context for customer business APIs.
4. Define platform-vs-company authorization policy, role seeding, permission naming, and the Accline Services administration boundary before building its UI.

## Dependencies

- PostgreSQL 16 is defined in Docker Compose and SQLAlchemy connects via `DATABASE_URL` or the `POSTGRES_*` environment fields.
- Alembic discovers `app.db.base.Base.metadata` after importing `app.models`.
- Future business modules must depend on the company-context/tenant-access foundation and add their own models in module files.

## Validation Needed

- P003 live Docker, Alembic, backend, test-suite, and frontend-build validation completed on 2026-09-08.
- Add PostgreSQL integration tests in CI before introducing transactional business workflows.
- Revisit role scope and company-owner policy after first-version testing; these decisions are provisional.
