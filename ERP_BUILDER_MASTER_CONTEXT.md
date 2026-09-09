# ERP Builder Master Context

## Purpose and use

This is the durable handover for ERP Builder. It records approved project context, completed milestones, deliberately deferred work, and open decisions. Read it with the relevant `AI_CONTEXT/` files before starting a new P-stage. Update it after every major P-stage as part of the documentation and backup practice.

**Repository:** `C:\Users\mukes\Workspace\ERP-Builder`  
**Current product name:** ERP Builder  
**Platform/operator:** Accline Services  
**Checkpoint:** P006 company, branch, and warehouse management complete and validated on 2026-09-09. P007 is not started.

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

### P003 database architecture

| Area | Tables | Approved foundation |
| --- | --- | --- |
| Identity | `users`, `authentication_methods` | A user is independent of a company and must have email or mobile contact information. One user can have one record per supported authentication-method type. |
| Tenancy | `companies`, `user_company_accesses` | A company is the tenant boundary. Users can have explicit active access to multiple companies. |
| Optional organization | `branches`, `warehouses` | Each belongs to a company; neither is required. A warehouse may optionally reference a branch in the same company. |
| RBAC | `roles`, `permissions`, `role_permissions`, `role_assignments` | Roles are platform- or company-scoped. Assignments can be global or company-specific. No role/permission catalogue is seeded. |

## Approved decisions and requirements

### Identity, authentication, and user management

- **IMPLEMENTED:** `email_password` and `mobile_otp` methods map to one `User`; the P004 flows enforce active, verified methods and account state before authentication.
- **IMPLEMENTED:** bcrypt password and OTP hashing, short-lived/single-use activation, verification, reset tokens and OTPs, server-side session invalidation, and generic credential/recovery responses.
- **DEFERRED:** user provisioning and management APIs/UI, customer-management UI, Accline Services administration UI, and paid/production notification-provider integration.
- **OPEN:** the initial company Owner assignment workflow. A company creator does not automatically receive Owner rights; Accline Services controls the primary Owner assignment.

### Tenancy, branches, warehouses, and RBAC

- **IMPLEMENTED foundation:** every future customer business API must require active `UserCompanyAccess` for the selected company; a client-supplied company identifier or frontend hiding is insufficient authorization.
- **IMPLEMENTED foundation:** `User.is_platform_admin` marks platform administration; platform access must be enforced server-side and is separate from customer administration.
- **IMPLEMENTED:** server-side authenticated user and active-company access checks for the P004 authentication endpoints; platform-admin authentication has a separate route and session boundary.
- **IMPLEMENTED:** P006 organization APIs independently validate an authenticated session and active `UserCompanyAccess` for the requested `X-Company-ID`; records cannot be read or changed across the selected company boundary. Warehouse-to-branch association is validated in the service layer for the same company.
- **DEFERRED:** role-scope enforcement, role/permission seeding, customer/platform administration workflows, and authorization for future business APIs beyond the P006 organization boundary.
- **OPEN:** detailed role/permission catalogue, customer-administrator policy after first-version testing, and subscription association/pricing policy.

### Application shell, experience, and customization

- **IMPLEMENTED:** responsive P005 authenticated application shell and dashboard foundation with desktop/mobile navigation, theme preferences, language-switcher foundation, centralized product branding configuration, and protected frontend routes.
- **PLANNED:** complete Hindi/Marathi translations, persistent user/default-company preferences, dashboard customization, company branding, and document/invoice layout customization.
- **OPEN:** detailed application information architecture after first-version review, supported-language translation scope, branding/customization scope, and document/invoice template model.

### Future capabilities and integrations

- **PLANNED:** WhatsApp and SMS integration; GST and e-way bill support; invoice/document QR-code and barcode capability; and an AI assistant.
- **DEFERRED:** all associated provider integrations, API/UI workflows, storage, billing, and operational processes.
- **OPEN:** providers, jurisdictions and compliance scope, integration boundaries, AI capabilities/data access, QR/barcode payload standards, and delivery sequencing.

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

## Documentation and handover practice

- Treat `AI_CONTEXT/` and this master context as durable collaboration records.
- Update this master context, current status, active task, next steps, and any affected decision/dependency/security documents after every major P-stage.
- Record completed work as **IMPLEMENTED**, authorized future work as **PLANNED**, intentionally postponed work as **DEFERRED**, and unresolved choices as **OPEN**. Do not invent a decision to fill a gap.
- Do not commit documentation checkpoints until reviewed and explicitly authorized.
