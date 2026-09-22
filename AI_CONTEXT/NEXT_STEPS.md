# Next Steps

## Immediate Next Steps

No successor product P-stage is authorized. P010 is **COMPLETE**; P010.1 backend/frontend are online and P010.1-B provides the pending one-time bootstrap command. P011 has not started.

When a future task is authorized, resolve or sequence these **OPEN** decisions first:

1. Account-provisioning workflow for Pruvian Technologies, including primary company Owner assignment and controlled company status/structure overrides.
2. Branch-level and warehouse-level authorization scope; P007 defaults are preferences and do not restrict authorization.
3. Advanced CRM, multiple-contact UI, advanced multiple-address management, GST calculations, e-invoice/e-way bill, configurable numbering, and sales/purchase transaction scope.
4. Full Pruvian Technologies platform-administration UI and policy workflow, separate from company administration.
5. Production notification-provider selection and operational controls for email/SMS/WhatsApp; P004 intentionally uses a development-only provider abstraction.
6. P011 stock movements/ledger, P012 sales, accounting/supplier ledger, full GST, advanced procurement/approvals/PDF/attachments, UOM conversions, price lists, barcode scanning/printing, and advanced image storage are not authorized or started.
7. Run the one-time bootstrap procedure in [`docs/STAGING_DEPLOYMENT.md`](../docs/STAGING_DEPLOYMENT.md), remove its Render secrets afterward, then founder-test the connected staging application before declaring staging accepted.

## Dependencies

- PostgreSQL 16 is defined in Docker Compose and SQLAlchemy connects via `DATABASE_URL` or the `POSTGRES_*` environment fields.
- Alembic discovers `app.db.base.Base.metadata` after importing `app.models`.
- P006 supplies the authenticated organization boundary: `/organization` requires an active session and `UserCompanyAccess` for `X-Company-ID`, then scopes every record query to that company. Branch/warehouse role scope remains deferred.
- P007 adds `/administration` company-permission checks with 8 standard roles and 30 current permissions; P005 company switching remounts both organization and P007 administration data without replacing server-side authorization.
- P008 adds company-scoped `/parties` customer/supplier operations behind active-company context and P007 permissions; customer/supplier screens remount and reload party data when the selected company changes.
- P010 adds company-scoped `/purchases` PO/GRN/Invoice operations behind the same boundary; P011 must consume accepted GRN goods facts without changing P010 into a stock ledger.
- P010.1 retains local Docker PostgreSQL configuration and uses the secret `DATABASE_URL` at staging runtime. Alembic must run to head before the FastAPI process begins.

## Validation Needed

- **COMPLETE:** P008 Alembic `e008a1b2c3d4`, PostgreSQL, health endpoints, 29 backend tests, 3 P008 tests, 18 prior-module regression tests, frontend TypeScript/production build, live customer/supplier create/edit/lifecycle, tenant isolation, readable validation errors, and founder visual review completed on 2026-09-17.
- **COMPLETE:** P010 Alembic `g010a1b2c3d4`, healthy PostgreSQL and health endpoints, 33 backend tests including 2 P010 tests, frontend TypeScript, and production build completed on 2026-09-17.
- Add PostgreSQL integration tests in CI before introducing transactional business workflows.
- Revisit branch/warehouse authorization scope, primary Owner assignment, and catalogue expansion when future transactional modules are authorized.
