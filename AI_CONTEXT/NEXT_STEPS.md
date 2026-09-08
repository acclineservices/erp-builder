# Next Steps

## Immediate Next Steps

No successor P-stage is authorized. P003 is **COMPLETE**; P004 and later work remain unstarted.

When a future task is authorized, resolve or sequence these **OPEN** decisions first:

1. Account-provisioning workflow for Accline Services, including primary company Owner assignment.
2. Detailed platform-vs-company authorization policy, role/permission catalogue, role seeding, and administration boundary.
3. Authentication-flow design for email/password and mobile OTP, including password hashing, OTP lifecycle, and recovery.
4. Application shell/navigation, language preferences, light/dark/system theme behavior, branding scope, and document/invoice layout customization.
5. Sequencing and provider/compliance choices for WhatsApp/SMS, GST/e-way bill, QR/barcode, and AI-assistant capabilities.

## Dependencies

- PostgreSQL 16 is defined in Docker Compose and SQLAlchemy connects via `DATABASE_URL` or the `POSTGRES_*` environment fields.
- Alembic discovers `app.db.base.Base.metadata` after importing `app.models`.
- Future business modules must depend on the company-context/tenant-access foundation and add their own models in module files.

## Validation Needed

- **COMPLETE:** P003 live Docker, Alembic, backend, test-suite, and frontend-build validation completed on 2026-09-08.
- Add PostgreSQL integration tests in CI before introducing transactional business workflows.
- Revisit role scope and company-owner policy after first-version testing; these decisions are provisional.
