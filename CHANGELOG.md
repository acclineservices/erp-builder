# Changelog

Notable approved repository changes are recorded here. This is not a task backlog.

## Unreleased

- No pending changes.

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
