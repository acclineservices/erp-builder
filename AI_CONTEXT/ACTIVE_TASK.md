# Active Task

## Task Identifier

P010 - Purchase Management Foundation

## Status

**COMPLETE** - completed and validated on 2026-09-17. Company-scoped Purchase Orders, GRNs, and Purchase Invoices, Decimal totals, lifecycle, P007 permissions/audit, tenant isolation, UI, migration, backend tests, and frontend build passed.

No successor implementation task is active. P011 has not started.

## Scope

Build company-scoped purchase document foundations without inventory posting, sales, accounting posting, or a full GST engine.

## Constraints

- Preserve active UserCompanyAccess as the tenant boundary and enforce P007 purchase permissions server-side.
- Keep stock ledger (P011), Sales (P012), accounting/supplier ledger, full GST, e-invoice/e-way bill, advanced approvals/PDFs/attachments deferred.
- Do not start P011.

## Definition of Done

- PO/GRN/Invoice records preserve commercial snapshots, use local numbering and Decimal totals, and enforce controlled lifecycle, audit, RBAC, and tenant isolation.
- `/app/purchases` reloads on company switching and uses the reusable safe API-error formatting.
- Validation records Alembic `g010a1b2c3d4`, 33 backend tests including 2 P010 tests, health endpoints, TypeScript, and production build.
