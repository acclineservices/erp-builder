# Next Steps

## Immediate Next Steps

No successor P-stage is authorized. P007 is **COMPLETE**; P008 has not started.

When a future task is authorized, resolve or sequence these **OPEN** decisions first:

1. Account-provisioning workflow for Accline Services, including primary company Owner assignment and controlled company status/structure overrides.
2. Branch-level and warehouse-level authorization scope; P007 defaults are preferences and do not restrict authorization.
3. Full Accline Services platform-administration UI and policy workflow, separate from company administration.
4. Production notification-provider selection and operational controls for email/SMS/WhatsApp; P004 intentionally uses a development-only provider abstraction.
5. First-version review of P005/P006 information architecture, translations, dashboard customization, company/default context behavior, company branding/logo storage, and document/invoice layout scope.
6. Sequencing and provider/compliance choices for WhatsApp/SMS, GST/e-way bill, QR/barcode, and AI-assistant capabilities.

## Dependencies

- PostgreSQL 16 is defined in Docker Compose and SQLAlchemy connects via `DATABASE_URL` or the `POSTGRES_*` environment fields.
- Alembic discovers `app.db.base.Base.metadata` after importing `app.models`.
- P006 supplies the authenticated organization boundary: `/organization` requires an active session and `UserCompanyAccess` for `X-Company-ID`, then scopes every record query to that company. Branch/warehouse role scope remains deferred.
- P007 adds `/administration` company-permission checks with 8 standard roles and 30 current permissions; P005 company switching remounts both organization and P007 administration data without replacing server-side authorization.

## Validation Needed

- **COMPLETE:** P007 Alembic `d07a3e1b4f91`, PostgreSQL, health endpoints, 26 backend tests, 5 P007 tests, 13 authentication/P006 regression tests, frontend TypeScript/production build, tenant isolation, and populated visual review completed on 2026-09-16.
- Add PostgreSQL integration tests in CI before introducing transactional business workflows.
- Revisit branch/warehouse authorization scope, primary Owner assignment, and catalogue expansion when future transactional modules are authorized.
