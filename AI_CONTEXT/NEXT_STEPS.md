# Next Steps

## Immediate Next Steps

No successor P-stage is authorized. P006 is **COMPLETE**; P007 is not started.

When a future task is authorized, resolve or sequence these **OPEN** decisions first:

1. P007 authorization policy, role/permission catalogue, role seeding, and company/platform administration workflows.
2. Account-provisioning workflow for Accline Services, including primary company Owner assignment and controlled company status/structure overrides.
3. Production notification-provider selection and operational controls for email/SMS/WhatsApp; P004 intentionally uses a development-only provider abstraction.
4. First-version review of P005/P006 information architecture, translations, dashboard customization, company/default context behavior, company branding/logo storage, and document/invoice layout scope.
5. Sequencing and provider/compliance choices for WhatsApp/SMS, GST/e-way bill, QR/barcode, and AI-assistant capabilities.

## Dependencies

- PostgreSQL 16 is defined in Docker Compose and SQLAlchemy connects via `DATABASE_URL` or the `POSTGRES_*` environment fields.
- Alembic discovers `app.db.base.Base.metadata` after importing `app.models`.
- P006 supplies the authenticated organization boundary: `/organization` requires an active session and `UserCompanyAccess` for `X-Company-ID`, then scopes every record query to that company. P007 should add policy checks at the organization service boundary.
- P005 protects its frontend shell with P004 session context; P006 company switching remounts organization data and does not replace server-side authorization.

## Validation Needed

- **COMPLETE:** P006 Alembic/PostgreSQL, 21 backend tests, P004 authentication regression, health endpoints, frontend TypeScript/production build, tenant-safe company switching, and secret review completed on 2026-09-09.
- Add PostgreSQL integration tests in CI before introducing transactional business workflows.
- Revisit role scope and company-owner policy after first-version testing; these decisions are provisional.
