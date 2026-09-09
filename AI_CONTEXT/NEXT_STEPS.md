# Next Steps

## Immediate Next Steps

No successor P-stage is authorized. P005 is **COMPLETE**; P006 is not started.

When a future task is authorized, resolve or sequence these **OPEN** decisions first:

1. Account-provisioning workflow for Accline Services, including primary company Owner assignment.
2. Detailed platform-vs-company authorization policy, role/permission catalogue, role seeding, and administration boundary.
3. Production notification-provider selection and operational controls for email/SMS/WhatsApp; P004 intentionally uses a development-only provider abstraction.
4. First-version review of P005 information architecture, translations, dashboard customization, company/default context behavior, branding, and document/invoice layout scope.
5. Sequencing and provider/compliance choices for WhatsApp/SMS, GST/e-way bill, QR/barcode, and AI-assistant capabilities.

## Dependencies

- PostgreSQL 16 is defined in Docker Compose and SQLAlchemy connects via `DATABASE_URL` or the `POSTGRES_*` environment fields.
- Alembic discovers `app.db.base.Base.metadata` after importing `app.models`.
- P004 supplies authenticated user context and an accessible-company list, but future business modules must still depend on explicit company-context/tenant-access checks and add their own models in module files.
- P005 protects its frontend shell with P004 session context but does not replace server-side authorization for future business APIs.

## Validation Needed

- **COMPLETE:** P005 frontend TypeScript/build, responsive shell, protected-route, login/logout, authorized-company, Docker health, and P004 regression validation completed on 2026-09-09.
- Add PostgreSQL integration tests in CI before introducing transactional business workflows.
- Revisit role scope and company-owner policy after first-version testing; these decisions are provisional.
