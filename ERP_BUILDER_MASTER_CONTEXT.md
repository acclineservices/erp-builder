# ERP Builder Master Context

## Purpose and use

This is the durable handover for ERP Builder. It records approved project context, completed milestones, deliberately deferred work, and open decisions. Read it with the relevant `AI_CONTEXT/` files before starting a new P-stage. Update it after every major P-stage as part of the documentation and backup practice.

**Repository:** `C:\Users\mukes\Workspace\ERP-Builder`  
**Current product name:** ERP Builder  
**Platform/operator:** Accline Services  
**Checkpoint:** P003 complete and published at `7bbbd3eb2f57f2105879c1a6c185b6b7f940a354` on `main` / `origin/main`.

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

### P003 database architecture

| Area | Tables | Approved foundation |
| --- | --- | --- |
| Identity | `users`, `authentication_methods` | A user is independent of a company and must have email or mobile contact information. One user can have one record per supported authentication-method type. |
| Tenancy | `companies`, `user_company_accesses` | A company is the tenant boundary. Users can have explicit active access to multiple companies. |
| Optional organization | `branches`, `warehouses` | Each belongs to a company; neither is required. Warehouses are not yet tied to branches. |
| RBAC | `roles`, `permissions`, `role_permissions`, `role_assignments` | Roles are platform- or company-scoped. Assignments can be global or company-specific. No role/permission catalogue is seeded. |

## Approved decisions and requirements

### Identity, authentication, and user management

- **IMPLEMENTED foundation:** `email_password` and `mobile_otp` authentication-method records map to the same `User` identity where both are enabled.
- **DEFERRED:** login, logout, password hashing implementation, OTP delivery/verification, recovery, user-management APIs, customer-management UI, and Accline Services administration UI.
- **Security requirement:** never store plaintext passwords or OTPs. Future passwords require an adaptive industry-standard hash; OTPs must be short-lived and protected by the future authentication mechanism.
- **OPEN:** the initial company Owner assignment workflow. A company creator does not automatically receive Owner rights; Accline Services controls the primary Owner assignment.

### Tenancy, branches, warehouses, and RBAC

- **IMPLEMENTED foundation:** every future customer business API must require active `UserCompanyAccess` for the selected company; a client-supplied company identifier or frontend hiding is insufficient authorization.
- **IMPLEMENTED foundation:** `User.is_platform_admin` marks platform administration; platform access must be enforced server-side and is separate from customer administration.
- **DEFERRED:** authentication/authorization middleware, role-scope enforcement, role/permission seeding, and administration workflows.
- **OPEN:** detailed role/permission catalogue, customer-administrator policy after first-version testing, subscription association/pricing policy, and the warehouse-to-branch relationship.

### Application shell, experience, and customization

- **IMPLEMENTED:** only the P002 responsive foundation page and backend-status feedback. It uses light/dark utility styling.
- **PLANNED:** a mobile-browser-capable product experience, language preferences, and light/dark/system theme preferences.
- **PLANNED:** theme and branding customization, plus document/invoice layout customization.
- **OPEN:** application shell/navigation information architecture, supported languages, default and persistence behavior for theme preference, branding scope, and document/invoice template model.

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

No P004 or later implementation has started.

## Documentation and handover practice

- Treat `AI_CONTEXT/` and this master context as durable collaboration records.
- Update this master context, current status, active task, next steps, and any affected decision/dependency/security documents after every major P-stage.
- Record completed work as **IMPLEMENTED**, authorized future work as **PLANNED**, intentionally postponed work as **DEFERRED**, and unresolved choices as **OPEN**. Do not invent a decision to fill a gap.
- Do not commit documentation checkpoints until reviewed and explicitly authorized.
