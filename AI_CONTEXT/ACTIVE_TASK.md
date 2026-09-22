# Active Task

## Task Identifier

P010.1-A - Prepare Pruvian for online staging deployment

## Status

**COMPLETE (repository preparation only)** - P010 purchase-management scope remains complete. P010.1 prepares Pruvian for Render staging; it does not create/connect services or mark online staging deployment complete.

No successor product implementation task is active. P011 has not started.

## Scope

Prepare safe deployment configuration, finalized brand naming, and Render staging instructions without inventory posting, sales, accounting posting, or a full GST engine.

## Constraints

- Preserve active UserCompanyAccess as the tenant boundary and enforce P007 purchase permissions server-side.
- Do not create or configure Render services from the repository task; staging remains pending connection and founder testing.
- Keep stock ledger (P011), Sales (P012), accounting/supplier ledger, full GST, e-invoice/e-way bill, advanced approvals/PDFs/attachments deferred.
- Do not start P011.

## Definition of Done

- Pruvian accepts a secret `DATABASE_URL`, supports HTTPS cookie/CORS configuration, and retains local Docker development defaults.
- Render deployment details document migration-before-start, port binding, frontend `VITE_API_BASE_URL`, and the SPA rewrite.
- P011 remains unstarted.
