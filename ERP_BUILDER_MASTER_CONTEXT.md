# ERP Builder Master Context

## Purpose and use

This is the durable handover for ERP Builder. It records approved project context, completed milestones, deliberately deferred work, and open decisions. Read it with the relevant `AI_CONTEXT/` files before starting a new P-stage. Update it after every major P-stage as part of the documentation and backup practice.

**Repository:** `C:\Users\mukes\Workspace\ERP-Builder`  
**Current product name:** ERP Builder  
**Platform/operator:** Accline Services  
**Checkpoint:** P010 purchase management foundation complete and validated on 2026-09-17. P011 has not started.

## Product purpose and principles

ERP Builder is the foundation for a long-term commercial SaaS ERP platform intended to make everyday business operations clearer and more manageable. Accline Services operates the platform. A `Company` represents the customer business and the fundamental tenant/data-isolation boundary.

- Start simple; avoid unnecessary complexity, speculative abstractions, dependencies, and premature business assumptions.
- Keep decisions testable and proportionate. Decisions may change after testing; record material changes rather than treating provisional choices as permanent.
- Keep product/business modules modular and company-scoped.
- ERP Builder is the current product/application name. It may change later; do not make the display name a durable architectural identifier or tenant boundary.

## Current delivery state

### IMPLEMENTED - P002 application foundation

- React, TypeScript, Vite, and Tailwind CSS frontend.
- A single responsive foundation/landing page with a backend-connection indicator; it supports light and dark styling.
- FastAPI backend with `GET /health`.
- This is not an approved authenticated application shell, information architecture, or navigation system.

### IMPLEMENTED - P003 identity and organization foundation

- Docker Compose development services for PostgreSQL 16, backend, and frontend.
- Environment-based backend configuration, SQLAlchemy 2.x, Alembic, and project-local database sessions.
- PostgreSQL migration `58d8a59c599f` with UUID identifiers, timestamps, foreign keys, unique constraints, indexes, and relevant checks.
- `GET /health/database` verifies database connectivity.
- Company-context primitive for future endpoints to check active user access to a requested company.
- Initial test coverage for database foundations and health endpoints.

### IMPLEMENTED - P004 authentication foundation

- Email/password login, first-time activation, email/mobile verification, email and mobile-OTP password reset, and mobile-OTP login foundation.
- Opaque, revocable server-side sessions with logout, fixed session timeout, optional Remember Me persistence, and temporary failed-login protection.
- `invited`, `active`, and `inactive` user account states; only active users authenticate.
- Separate platform-admin authentication routes and session cookie boundary.
- Authenticated-user context (`/auth/me`) and accessible-company listing restricted to active `UserCompanyAccess` records.
- P004 migration `b71f4e9c2a10` adds user-state fields plus `sessions`, `auth_tokens`, `otp_challenges`, and `security_events`.
- Passwords, OTPs, and single-use tokens are stored only as hashes. Development notification delivery is an in-memory provider abstraction; no production email, SMS, or WhatsApp provider is integrated.

### IMPLEMENTED - P005 application shell and navigation

- Clean frontend route handling separates /auth from protected /app shell routes; unauthenticated navigation is returned to authentication and logout returns to /auth.
- Responsive application shell with a collapsible desktop sidebar and mobile drawer, header, breadcrumbs, global-search foundation, quick actions, notification/help/profile entry points, and placeholder navigation for future ERP modules.
- Role-aware dashboard foundation clearly labels non-transactional placeholder content and does not fabricate financial or operational data.
- Authorized company context is loaded only from the P004 company endpoint; single-company users have compact context display and multi-company users have a header switcher. Last-used selection is stored locally and revalidated against returned access.
- Centralized product brand configuration, design tokens, and light/dark/system preferences; language preference foundation supports English, Hindi, and Marathi without claiming completed translations.

### IMPLEMENTED - P006 company, branch, and warehouse management

- Company profile/setup is available only in the selected authenticated company context, with legal/display names, extensible business type, optional GST/contact/address information, company status display, logo URL foundation, and a lightweight profile-completion indicator. Accline Services retains company status and subscription control; billing is not implemented.
- Branches remain optional: no synthetic head-office branch is created. Authorized company-context users can list, create, edit, and activate/deactivate company-scoped branches.
- Warehouses remain optional: no synthetic warehouse is created. Warehouses can be listed, created, edited, and activated/deactivated, and may have an optional branch from the same company only.
- P006 migration `c83a91d4e6f2` adds only optional organization profile/location fields and the optional warehouse `branch_id` relation.
- `/organization` endpoints require an authenticated session plus active `UserCompanyAccess` for `X-Company-ID`; every branch and warehouse lookup is constrained to that active company. P007 can add role policy checks at the service boundary without weakening tenant isolation.

### IMPLEMENTED - P007 user, role, and permission management

- Company-scoped user management supports invitations through the existing activation flow, active/inactive company access, multiple role assignments, default branch/warehouse preferences, force logout, secure reset/activation initiation, and administrative audit events.
- Each company receives eight fixed system-managed standard roles: Owner, Admin, Accountant, Sales User, Purchase User, Inventory User, Store Manager, and Viewer. Custom company roles can be created, edited, activated, and cloned.
- The current granular permission catalogue contains 30 permissions. Effective permissions are additive across a user's active company role assignments; administrators cannot grant permissions they do not hold, and the system-managed Owner role is protected from ordinary company administration.
- P007 migration `d07a3e1b4f91` makes roles company-scoped, adds company defaults to access grants, and adds company-scoped user-management audit events.
- `/administration` enforces an authenticated active company context and required company permissions on every action. Cross-company access is rejected; branch and warehouse values remain convenience defaults, not authorization boundaries.
- The protected `/app/users` route provides company-scoped Users, Roles, Permissions, and Security administration UI and reloads its administration data when the selected company changes.

### IMPLEMENTED - P008 customer and supplier management

- A shared company-scoped `Party` foundation supports Customer, Supplier, and Both, with primary contact/address records, GST/PAN identity fields, commercial fields, active/inactive lifecycle, and searchable customer/supplier views.
- Customer and supplier codes are generated independently per company (`CUS-0001` and `SUP-0001` style). GSTIN is required for registered/composition parties; GSTIN, PAN, and company-local code/GSTIN uniqueness are validated server-side.
- `/parties` requires authenticated active-company context and P007 customer/supplier permissions. Every lookup is company-scoped, including a cross-company object-ID `404`; create, update, and lifecycle actions write company audit events.
- Protected `/app/customers` and `/app/suppliers` provide customer/supplier management, company-switching reload, search/filter, edit, and lifecycle controls. A reusable frontend API-error formatter turns FastAPI validation detail arrays into safe, readable messages.

### IMPLEMENTED - P009 product and item master management

- Shared company-scoped Items support Goods and Services with categories, controlled UOMs, company-local `ITEM-0001` codes, HSN/SAC, allowed GST-rate references, decimal pricing, barcode/image foundations, lifecycle, and search/filter.
- Goods may carry inventory setup fields and an optional same-company default warehouse; Services reject inventory fields. Opening stock is stored only as setup foundation, with no stock ledger or movement.
- `/items` uses active company context, P007 item permissions, company-scoped references/uniqueness, and audit events. `/app/items` and `/app/items/categories` reload on company switch.

### IMPLEMENTED - P010 purchase management foundation

- Company-scoped Purchase Orders, Goods Receipts (GRNs), and Purchase Invoices preserve supplier/item/UOM/description/rate/tax snapshots, Decimal totals, and `PO-0001`, `GRN-0001`, and `PI-0001` company-local numbering.
- PO drafts can be submitted, approved, or cancelled; GRNs can be cancelled; invoice drafts can be approved or cancelled. All operations use active company context, P007 purchase permissions, same-company supplier/item/warehouse/document validation, and audit events.
- GRNs retain accepted/rejected Goods receipt facts but create no stock ledger or item balance. Purchase invoices retain commercial/due-date foundations but create no supplier ledger or journal posting. `/app/purchases` is a company-switch-safe responsive workspace.
- P010 enhancement adds editable draft documents, multi-line entry, PO-to-GRN and PO/GRN-to-invoice prefills, source-line references, partial/multiple Goods receipts, remaining-quantity checks, and linked-document actions. Migration `h010a1b2c3d4` adds invoice source-line traceability only.
- P010 entry enhancement adds reusable searchable supplier/item controls, explicitly blank manual lines, linked-plus-manual invoice lines, and browser-print voucher views. Advanced template/PDF generation remains deferred.

### P003 database architecture

| Area | Tables | Approved foundation |
| --- | --- | --- |
| Identity | `users`, `authentication_methods` | A user is independent of a company and must have email or mobile contact information. One user can have one record per supported authentication-method type. |
| Tenancy | `companies`, `user_company_accesses` | A company is the tenant boundary. Users can have explicit active access to multiple companies. |
| Optional organization | `branches`, `warehouses` | Each belongs to a company; neither is required. A warehouse may optionally reference a branch in the same company. |
| RBAC | `roles`, `permissions`, `role_permissions`, `role_assignments`, `user_management_audit_events` | P007 seeds 8 fixed company roles and 30 current permissions on demand; company assignments produce additive effective permissions. |
| Parties | `parties`, `party_contacts`, `party_addresses`, `party_code_sequences` | P008 stores one company-scoped business party as Customer, Supplier, or Both; contacts/addresses are extensible foundations and counters generate company-local customer/supplier codes. |

## Approved decisions and requirements

### Identity, authentication, and user management

- **IMPLEMENTED:** `email_password` and `mobile_otp` methods map to one `User`; the P004 flows enforce active, verified methods and account state before authentication.
- **IMPLEMENTED:** bcrypt password and OTP hashing, short-lived/single-use activation, verification, reset tokens and OTPs, server-side session invalidation, and generic credential/recovery responses.
- **IMPLEMENTED:** P007 company-scoped user provisioning/management UI and APIs, invitation/activation integration, role administration, safe security actions, and audit events.
- **DEFERRED:** Accline Services platform-administration UI and paid/production notification-provider integration.
- **OPEN:** the initial company Owner assignment workflow. A company creator does not automatically receive Owner rights; Accline Services controls the primary Owner assignment.

### Tenancy, branches, warehouses, and RBAC

- **IMPLEMENTED foundation:** every future customer business API must require active `UserCompanyAccess` for the selected company; a client-supplied company identifier or frontend hiding is insufficient authorization.
- **IMPLEMENTED foundation:** `User.is_platform_admin` marks platform administration; platform access must be enforced server-side and is separate from customer administration.
- **IMPLEMENTED:** server-side authenticated user and active-company access checks for the P004 authentication endpoints; platform-admin authentication has a separate route and session boundary.
- **IMPLEMENTED:** P006 organization APIs independently validate an authenticated session and active `UserCompanyAccess` for the requested `X-Company-ID`; records cannot be read or changed across the selected company boundary. Warehouse-to-branch association is validated in the service layer for the same company.
- **IMPLEMENTED:** P007 seeds fixed company roles and the current permission catalogue, requires active company access plus required permission for `/administration`, and prevents Owner mutation and administrator privilege escalation.
- **IMPLEMENTED:** P008 `/parties` requires the same active-company boundary plus P007 customer/supplier permission checks, scopes every Party query to the authorized company, and records party administration audit events.
- **DEFERRED:** branch-level and warehouse-level authorization scope, full Accline Services platform administration UI, and transactional-module permission enforcement until those modules exist.
- **OPEN:** initial primary Owner assignment workflow, catalogue expansion as ERP modules are introduced, customer-administrator policy after first-version testing, and subscription association/pricing policy.

### Application shell, experience, and customization

- **IMPLEMENTED:** responsive P005 authenticated application shell and dashboard foundation with desktop/mobile navigation, theme preferences, language-switcher foundation, centralized product branding configuration, and protected frontend routes.
- **PLANNED:** complete Hindi/Marathi translations, persistent user/default-company preferences, dashboard customization, company branding, and document/invoice layout customization.
- **OPEN:** detailed application information architecture after first-version review, supported-language translation scope, branding/customization scope, and document/invoice template model.

### Future capabilities and integrations

- **PLANNED:** WhatsApp and SMS integration; GST and e-way bill support; invoice/document QR-code and barcode capability; and an AI assistant.
- **DEFERRED:** all associated provider integrations, API/UI workflows, storage, billing, and operational processes.
- **OPEN:** providers, jurisdictions and compliance scope, integration boundaries, AI capabilities/data access, QR/barcode payload standards, and delivery sequencing.

### P010 boundaries

- **DEFERRED:** P011 inventory posting/stock ledger, P012 sales, accounting posting/supplier ledger, full GST engine and returns, e-invoice/e-way bill, advanced approvals/procurement, PDF templates, and attachment storage.

## Security and operational requirements

- Keep secrets in environment configuration. Never commit `.env`, production credentials, API keys, plaintext passwords, or plaintext OTPs.
- Use separate development, test, and production databases; automated tests must never target production data.
- Apply schema changes only through reviewed Alembic migrations.
- Enforce UUID identities, database constraints, tenant isolation, and server-side authorization; never rely on the frontend for access control.
- Do not expose credential hashes or authentication internals in API response schemas.

## Validation and checkpoint

P003 live validation completed on 2026-09-08:

- PostgreSQL Compose database service was healthy.
- `alembic upgrade head` succeeded; revision is `58d8a59c599f` with no pending migrations.
- All ten P003 foundation tables were present.
- `GET /health` returned `{"status":"ok"}`.
- `GET /health/database` confirmed PostgreSQL connectivity.
- Backend tests: 8 passed (two non-blocking third-party deprecation warnings).
- Frontend production build passed.
- Commit `7bbbd3eb2f57f2105879c1a6c185b6b7f940a354` (`P003: Complete database foundation`) was pushed and verified on `origin/main`.

P004 live validation completed on 2026-09-09:

- Docker 29.7.2, Python 3.12.10, the project virtual environment, and PostgreSQL Compose service were verified healthy.
- `alembic upgrade head` reached `b71f4e9c2a10`; all P004 authentication tables were present.
- `GET /health` and `GET /health/database` returned `{"status":"ok"}`.
- Backend tests: 18 passed, including 10 authentication tests; frontend production build passed.
- Invalid live login returned the generic `401 Invalid credentials.` response. Tests cover inactive-user blocking, company access restriction, logout/session invalidation, OTP expiry/attempt limits, activation, verification, and resets.
- No tracked `.env`, plaintext credential/OTP/token persistence, response secret leakage, or unrelated generated artifacts were found.

P005 live validation completed on 2026-09-09:

- Frontend TypeScript check and production build passed.
- Backend regression suite passed: 18 tests, including 10 authentication tests.
- Health and database-health endpoints returned status ok.
- A development-only review identity authenticated through the unchanged P004 flow, received only its two active UserCompanyAccess companies, and was rejected after logout.
- Docker Compose serves the review application at http://localhost:5173; desktop/tablet/mobile layouts use CSS breakpoints, a collapsible desktop sidebar, and a mobile drawer.

P006 live validation completed on 2026-09-09:

- PostgreSQL Compose remained healthy and `alembic upgrade head` reached `c83a91d4e6f2`.
- `GET /health` returned `{"status":"ok"}` and `GET /health/database` returned `{"status":"ok","database":"available"}`.
- Backend tests: 21 passed, including P004 authentication regression tests and P006 company/branch/warehouse tenant-isolation, same-company branch-association, lifecycle, and zero-location tests.
- Frontend TypeScript and production build passed. Live development authentication verified two authorized company contexts, context-specific organization reads, and logout invalidation.
- No tracked `.env`, plaintext credential/OTP/token persistence, response secret leakage, or unrelated generated artifacts were found. Browser automation was unavailable in the validation environment; responsive layouts were verified through the implemented CSS breakpoints and production build.

P007 live validation completed on 2026-09-16:

- PostgreSQL Compose was healthy; `alembic upgrade head` reached `d07a3e1b4f91`; `/health` and `/health/database` passed.
- The full backend suite passed: 26 tests. The dedicated P007 suite passed: 5 tests. Authentication/P006 regressions passed: 13 tests.
- Live P007 bootstrap returned the expected populated company data; cross-company access returned `403`. Tenant isolation, Owner protection, and administrator privilege-escalation prevention were validated.
- Frontend TypeScript and production build passed. Founder visual review confirmed the populated Users & Roles UI, including Users, Roles, Permissions, and Security administration, is readable in light and dark themes.

P008 live validation completed on 2026-09-17:

- PostgreSQL Compose was healthy and Alembic reached `e008a1b2c3d4`; `/health` and `/health/database` returned 200.
- The full backend suite passed: 29 tests. The dedicated P008 suite passed: 3 tests. Authentication/P006/P007 regressions passed: 18 tests. Frontend TypeScript and production build passed.
- Live customer/supplier create, generated codes, contact/address persistence, edit, lifecycle, search/filter, readable validation errors, tenant isolation, and permission enforcement passed. Founder visual review approved Customers and Suppliers in light/dark and mobile layouts.
- Advanced CRM, multiple-contact UI, advanced multi-address management, GST calculations, e-invoice/e-way bill, sales/purchase transactions, configurable numbering, and P009 remain deferred.

P010 live validation completed on 2026-09-17:

- Docker PostgreSQL was healthy; Alembic reached `g010a1b2c3d4`; `/health` and `/health/database` returned 200.
- Full backend suite passed: 33 tests, including 2 dedicated P010 purchase workflow/security tests. Frontend TypeScript and production build passed.
- Validation covers company-local numbering, authoritative Decimal line totals, PO lifecycle, Goods-only GRNs, tenant/foreign-reference and permission rejection, audit events, zero-warehouse operation, and company-resetting UI data loads.

## Documentation and handover practice

- Treat `AI_CONTEXT/` and this master context as durable collaboration records.
- Update this master context, current status, active task, next steps, and any affected decision/dependency/security documents after every major P-stage.
- Record completed work as **IMPLEMENTED**, authorized future work as **PLANNED**, intentionally postponed work as **DEFERRED**, and unresolved choices as **OPEN**. Do not invent a decision to fill a gap.
- Do not commit documentation checkpoints until reviewed and explicitly authorized.
