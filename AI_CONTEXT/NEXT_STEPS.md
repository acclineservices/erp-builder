# Next Steps

## Immediate Next Steps

No successor P-stage is authorized. P004 is **COMPLETE**; P005 is not started.

When a future task is authorized, resolve or sequence these **OPEN** decisions first:

1. Account-provisioning workflow for Accline Services, including primary company Owner assignment.
2. Detailed platform-vs-company authorization policy, role/permission catalogue, role seeding, and administration boundary.
3. Production notification-provider selection and operational controls for email/SMS/WhatsApp; P004 intentionally uses a development-only provider abstraction.
4. Application shell/navigation, language preferences, light/dark/system theme behavior, branding scope, and document/invoice layout customization.
5. Sequencing and provider/compliance choices for WhatsApp/SMS, GST/e-way bill, QR/barcode, and AI-assistant capabilities.

## Dependencies

- PostgreSQL 16 is defined in Docker Compose and SQLAlchemy connects via `DATABASE_URL` or the `POSTGRES_*` environment fields.
- Alembic discovers `app.db.base.Base.metadata` after importing `app.models`.
- P004 supplies authenticated user context and an accessible-company list, but future business modules must still depend on explicit company-context/tenant-access checks and add their own models in module files.

## Validation Needed

- **COMPLETE:** P004 live Docker, Alembic, health, backend test-suite (18 passed), authentication, security, and frontend-build validation completed on 2026-09-09.
- Add PostgreSQL integration tests in CI before introducing transactional business workflows.
- Revisit role scope and company-owner policy after first-version testing; these decisions are provisional.
