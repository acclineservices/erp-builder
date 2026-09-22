# Changelog

Notable approved repository changes are recorded here. This is not a task backlog.

## 2026-09-22 - P010.1: Add secure staging bootstrap

- Added an idempotent, staging-only CLI for creating the first verified company Owner from Render environment variables, using the existing P003/P004/P007 data and role-catalogue foundations.
- The command has no HTTP route, never prints credential material, and leaves platform-administration access disabled.
- Validated by 42 backend tests; the one-time Render invocation remains an operator-controlled action.

## 2026-09-22 - P010.1: Prepare Pruvian for staging deployment

- Finalized customer-facing Pruvian Technologies / Pruvian branding, tagline, and platform description while preserving Pruvian ERP internal naming.
- Prepared Render-safe PostgreSQL URL handling, explicit credentialed CORS, HTTPS session-cookie configuration, centralized Vite API base URL handling, and documented backend/static-site deployment configuration including Alembic startup and SPA rewrites.
- Validated Alembic head `h010a1b2c3d4`, 39 backend tests, and frontend TypeScript/production build.
- This checkpoint does not create Render services or mark online staging deployment complete. P011 has not started.

## 2026-09-17 - P010: Improve purchase entry and voucher printing

- Added reusable searchable selectors, blank manual item lines, manual invoice items beside linked lines, PO-linked GRN line control, and direct browser-print PO/GRN/Invoice vouchers with A4 print CSS.
- Advanced document templates, PDF generation, email/WhatsApp sharing, and QR output remain deferred.

## 2026-09-17 - P010: Complete linked multi-line purchase workflow

### Added

- Editable draft PO, GRN, and invoice forms with multiple lines, add/remove controls, immediate previews, detail actions, and source-prefilled PO → GRN and PO/GRN → Invoice flows.
- Partial/multiple GRN foundation, remaining-quantity validation, PO receipt-status updates, and invoice PO/GRN-line traceability migration `h010a1b2c3d4`.

### Validated

- Full backend suite: 34 passed, including linked P010 workflow tests. PostgreSQL migration, health endpoints, TypeScript, and frontend production build passed.

## 2026-09-17 - P010: Implement purchase management foundation

### Added

- Migration `g010a1b2c3d4` for company-scoped Purchase Orders, PO lines, Goods Receipts/GRN lines, Purchase Invoices/invoice lines, and per-company purchase document sequences.
- Tenant-safe `/purchases` APIs and `/app/purchases` workspace for PO, GRN, and invoice creation, lifecycle actions, Decimal totals, supplier/item snapshots, company-local `PO-0001`/`GRN-0001`/`PI-0001` numbering, P007 permissions, and audit events.

### Deferred

- P011 inventory posting/stock ledger, P012 Sales, accounting/supplier-ledger posting, full GST, e-invoice/e-way bill, advanced approvals, document templates, and attachment storage.

### Validated

- PostgreSQL healthy; Alembic at `g010a1b2c3d4`; `/health` and `/health/database` passed.
- Full backend suite: 33 passed, including 2 P010 tests. Frontend TypeScript and production build passed.

## 2026-09-17 - P009: Implement product and item master management

### Added

- Migration `f009a1b2c3d4` with company-scoped item categories, items, and item-code sequences.
- Goods/Service item APIs and UI with controlled UOMs, codes, pricing, tax references, inventory setup foundation, category, barcode/image, lifecycle, search, P007 RBAC, tenant isolation, and audit events.

### Validated

- Alembic head, health endpoints, 31 backend tests including 2 P009 tests, and frontend production build passed.

## 2026-09-17 - P008: Implement customer and supplier management

### Added

- Migration `e008a1b2c3d4` for company-scoped shared Party records, extensible primary contact/address foundations, and locked customer/supplier code sequences.
- Tenant-safe `/parties` API and services for Customer, Supplier, and Both with company-local `CUS-0001`/`SUP-0001` codes, GST/PAN validation, commercial fields, search/filter, active/inactive lifecycle, P007 permission checks, and party audit events.
- Protected `/app/customers` and `/app/suppliers` management UI, navigation integration, company-switching reload, and a reusable API validation-error formatter that prevents structured FastAPI errors from rendering as `[object Object]`.

### Validated

- PostgreSQL healthy; Alembic at `e008a1b2c3d4`; `/health` and `/health/database` passed.
- Full backend suite: 29 passed. P008 suite: 3 passed. Authentication/P006/P007 regressions: 18 passed. Frontend TypeScript and production build passed.
- Live Customer/Supplier create, generated codes, contact/address persistence, edit, lifecycle, search/filter, readable validation errors, tenant isolation, and permission enforcement passed. Founder visual review approved Customers/Suppliers in light/dark and mobile layouts. No review credentials, temporary records, or `.env` files were committed.

## 2026-09-16 - P007: Implement user role and permission management

### Added

- Migration `d07a3e1b4f91` for company-scoped roles, system-managed role state, company default branch/warehouse preferences, and company user-management audit events.
- Tenant-safe `/administration` API and services for company user invitations/activation integration, active/inactive access, multiple roles, custom roles, cloning, additive permissions, safe reset/activation initiation, force logout, and audit events.
- Eight fixed system-managed company roles and 30 current granular permissions, with Owner protection and administrator privilege-escalation prevention.
- Protected `/app/users` Users, Roles, Permissions, and Security administration UI with company-switching data reload.

### Validated

- PostgreSQL healthy; Alembic at `d07a3e1b4f91`; `/health` and `/health/database` passed.
- Full backend suite: 26 passed. P007 suite: 5 passed. Authentication/P006 regressions: 13 passed.
- Live P007 bootstrap, tenant isolation, cross-company `403`, Owner protection, privilege-escalation prevention, frontend TypeScript/production build, and populated light/dark founder visual review passed. No review credentials, local-only fixtures, or `.env` files were committed.

## 2026-09-09 - P006: Implement company, branch and warehouse management

### Added

- Migration `c83a91d4e6f2` with additive company profile/setup fields, optional branch/warehouse location/contact fields, and optional warehouse-to-branch relation.
- Authenticated, tenant-scoped organization API and service boundary. Every request validates active `UserCompanyAccess` for `X-Company-ID`; branch/warehouse object reads and updates are scoped to that company, and warehouse branch association is same-company only.
- Setup screens for company profile/progress, optional branches, optional warehouses, empty states, lifecycle controls, and company-switcher-safe data refresh. Logo support is a storage-agnostic URL foundation only.

### Validated

- PostgreSQL healthy; Alembic at `c83a91d4e6f2`; `/health` and `/health/database` passed.
- 21 backend tests passed, including P004 authentication regression and P006 tenant-isolation, lifecycle, zero-location, and warehouse-branch validation tests.
- Frontend TypeScript/production build passed. Live development login, two-company context reads, and logout invalidation passed. No `.env` tracking, plaintext secret persistence, response secret leakage, or unrelated generated artifacts found.

## 2026-09-09 - P005: Implement application shell and navigation

### Added

- Protected frontend route foundation, responsive app shell, collapsible sidebar, mobile drawer, header, breadcrumbs, company switcher, profile/logout menu, search, quick-action, notification, help, and assistant placement foundations.
- Dashboard and navigation placeholders that explicitly contain no business functionality or fabricated operational data.
- Centralized brand configuration, design tokens, light/dark/system theme preference, and English/Hindi/Marathi language preference foundation.

### Validated

- Frontend TypeScript and production build, Docker Compose frontend review service, live P004 login/logout/company access, health endpoints, and 18 backend regression tests.

## 2026-09-09 - P004: Finalize authentication foundation

### Added

- Migration `b71f4e9c2a10`, email/password and mobile-OTP authentication, activation/verification, recovery, account states, session/logout behavior, Remember Me, failed-login protection, platform-admin authentication, and authenticated company listing.
- Development notification-provider abstraction with hashed password, OTP, session, and token persistence; no production delivery provider.

### Validated

- Docker/PostgreSQL, Alembic at `b71f4e9c2a10`, `/health`, `/health/database`, 18 backend tests including 10 authentication tests, frontend production build, and secret-leakage review.
- Migration batch-operation compatibility for SQLite upgrade/downgrade tests.

## 2026-09-08 - P003: Complete database foundation

### Added

- PostgreSQL 16 Docker development environment, SQLAlchemy 2.x, Alembic, and migration `58d8a59c599f`.
- Identity, authentication-method, company, user-company-access, branch, warehouse, and RBAC database foundations.
- Database health endpoint, P003 automated tests, and developer documentation.

### Validated

- Live PostgreSQL migration and table verification.
- Backend health and database-connectivity endpoints, complete backend test suite, and frontend production build.
- Published checkpoint: `7bbbd3eb2f57f2105879c1a6c185b6b7f940a354` on `origin/main`.
