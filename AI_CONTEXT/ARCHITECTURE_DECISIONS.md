# Architecture Decisions

## AD-001 — PostgreSQL through Docker for development

**Context:** ERP Builder needs a relational, multi-tenant-ready datastore without requiring developers to install PostgreSQL directly on Windows.

**Decision:** Use PostgreSQL 16 in the existing Docker Compose environment. Configure it solely with environment variables.

**Consequences:** Local runtime validation requires a running Docker daemon. Credentials remain outside source control in `.env`.

## AD-002 — SQLAlchemy 2.x and Alembic for persistence

**Context:** Future modules need independently maintained models and repeatable schema evolution.

**Decision:** Use SQLAlchemy 2.x declarative models split by domain, with shared metadata/timestamp infrastructure. Use Alembic with metadata autogeneration and committed migration revisions.

**Consequences:** Schema changes must be delivered through migrations, not ad-hoc database edits. Models are imported centrally only for migration discovery.

## AD-003 — Company is the business-data isolation boundary

**Context:** ERP Builder is a multi-tenant SaaS product in which customer business data must not cross company boundaries.

**Decision:** A `Company` is a first-class entity. `UserCompanyAccess` explicitly grants a user active access to a company, and future business APIs must resolve an active company context before operating on company data.

**Consequences:** One user can access many companies. Future business entities must be scoped to the applicable company. The current helper is structural groundwork, not completed authentication/authorization middleware.

## AD-004 — Branches and warehouses are optional company structures

**Context:** SMEs may begin without branches or warehouses and add them later.

**Decision:** `Branch` and `Warehouse` each belong to a company, but no company is required to have either.

**Consequences:** Future modules must not assume a branch or warehouse exists. Warehouse is not tied to a branch at this stage.

## AD-005 — Roles can be platform-scoped or company-scoped

**Context:** Accline Services needs backend-enforceable separation from normal customer administration, while company access needs future RBAC flexibility.

**Decision:** Store role scope (`platform` or `company`), permissions, role-permission grants, and user role assignments. `User.is_platform_admin` is an explicit platform-administration marker; it is not a frontend-only convention.

**Consequences:** Future authorization must enforce role scope and platform access server-side. No roles or permissions are seeded yet.

## AD-006 — Authentication methods represent one user identity

**Context:** Email/password and mobile/OTP must not create duplicate user accounts.

**Decision:** A user may have one minimal `AuthenticationMethod` record per method type, both linked to the same `User`. The model permits an optional `credential_hash` for a future password hash and has no OTP storage.

**Consequences:** Login, OTP delivery, verification, credential hashing, and recovery remain future work. Plaintext passwords and OTPs are prohibited.

## Provisional Decisions

The initial Owner assignment workflow, detailed role/permission catalogue, subscription association, warehouse-to-branch relationship, and administrative policy are intentionally provisional and must be reviewed after first-version testing.
