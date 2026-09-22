# Active Task

## Task Identifier

P010.1-B - Safe one-time staging bootstrap

## Status

**COMPLETE (repository checkpoint)** - P010 purchase-management scope remains complete. Staging backend and frontend are online; P010.1-B adds the validated guarded first-company/Owner bootstrap command. Its one-time Render execution remains manual.

No successor product implementation task is active. P011 has not started.

## Scope

Prepare a staging-only, environment-driven initial company/Owner bootstrap command without inventory posting, sales, accounting posting, or a full GST engine.

## Constraints

- Preserve active UserCompanyAccess as the tenant boundary and enforce P007 purchase permissions server-side.
- Do not create a public bootstrap endpoint, emit credentials, or make the bootstrap user a platform admin.
- Keep stock ledger (P011), Sales (P012), accounting/supplier ledger, full GST, e-invoice/e-way bill, advanced approvals/PDFs/attachments deferred.
- Do not start P011.

## Definition of Done

- The command runs only with `APP_ENV=staging`, reads bootstrap inputs only from environment variables, and reuses P003/P004/P007 models and role catalogue seeding.
- It is idempotent and creates/reuses an active verified user, active company/access, and standard Owner assignment without a public endpoint.
- P011 remains unstarted.
