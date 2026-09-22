# Architecture Decisions

## AD-001 — PostgreSQL through Docker for development

**Context:** Pruvian ERP needs a relational, multi-tenant-ready datastore without requiring developers to install PostgreSQL directly on Windows.

**Decision:** Use PostgreSQL 16 in the existing Docker Compose environment. Configure it solely with environment variables.

**Consequences:** Local runtime validation requires a running Docker daemon. Credentials remain outside source control in `.env`.

## AD-002 — SQLAlchemy 2.x and Alembic for persistence

**Context:** Future modules need independently maintained models and repeatable schema evolution.

**Decision:** Use SQLAlchemy 2.x declarative models split by domain, with shared metadata/timestamp infrastructure. Use Alembic with metadata autogeneration and committed migration revisions.

**Consequences:** Schema changes must be delivered through migrations, not ad-hoc database edits. Models are imported centrally only for migration discovery.

## AD-003 — Company is the business-data isolation boundary

**Context:** Pruvian is a multi-tenant SaaS product in which customer business data must not cross company boundaries.

**Decision:** A `Company` is a first-class entity. `UserCompanyAccess` explicitly grants a user active access to a company, and future business APIs must resolve an active company context before operating on company data.

**Consequences:** One user can access many companies. Future business entities must be scoped to the applicable company. The current helper is structural groundwork, not completed authentication/authorization middleware.

## AD-004 — Branches and warehouses are optional company structures

**Context:** SMEs may begin without branches or warehouses and add them later.

**Decision:** `Branch` and `Warehouse` each belong to a company, but no company is required to have either. A warehouse may optionally reference a branch owned by that same company.

**Consequences:** Future modules must not assume a branch or warehouse exists. The P006 service validates the optional warehouse branch association before persistence, preventing cross-company links.

## AD-005 — Roles can be platform-scoped or company-scoped

**Context:** Pruvian Technologies needs backend-enforceable separation from normal customer administration, while company access needs future RBAC flexibility.

**Decision:** Store role scope (`platform` or `company`), permissions, role-permission grants, and user role assignments. `User.is_platform_admin` is an explicit platform-administration marker; it is not a frontend-only convention.

**Consequences:** P007 enforces company-scoped administration permissions server-side. Platform administration remains a separate future workflow and UI.

## AD-006 — Authentication methods represent one user identity

**Context:** Email/password and mobile/OTP must not create duplicate user accounts.

**Decision:** A user may have one minimal `AuthenticationMethod` record per method type, both linked to the same `User`. The model permits an optional `credential_hash` for a future password hash and has no OTP storage.

**Consequences:** Login, OTP delivery, verification, credential hashing, and recovery remain future work. Plaintext passwords and OTPs are prohibited.

## AD-007 - Product name is not a durable architectural identifier

**Context:** Pruvian is the finalized customer-facing product name; the internal project name remains Pruvian ERP.

**Decision:** Treat product and presentation naming as configurable context, not as a tenant boundary, durable integration identifier, or irreversible architectural assumption.

**Consequences:** Branding changes do not redefine company isolation or platform architecture. The detailed branding/customization model remains open.

## AD-008 - Revocable opaque sessions and provider-agnostic authentication delivery

**Context:** P004 requires browser authentication without exposing credentials, recovery values, or session internals to clients, while production email/SMS/WhatsApp providers remain undecided.

**Decision:** Store only bcrypt password/OTP digests and SHA-256 digests of opaque session and single-use token values. Authenticate through `User` and enabled, verified `AuthenticationMethod` records; persist revocable sessions with normal or Remember Me expiry. Keep platform-admin sessions in a separate route and cookie boundary. Use an in-memory development notification provider and do not integrate a paid production provider.

**Consequences:** Logout and password reset can invalidate server-side sessions; short-lived OTPs and tokens are attempt-limited or single-use. Production notification delivery, user provisioning, RBAC enforcement, and administration workflows remain separate decisions.

## AD-009 - Lightweight protected application shell with local presentation preferences

**Context:** P005 needs a reviewable authenticated product surface before a full information architecture, translation scope, dashboard model, or UI framework is approved.

**Decision:** Use a small React browser-history route layer and reusable shell components rather than adding a routing or UI-framework dependency. Gate frontend app routes through the existing P004 session endpoint and load company choices only through the existing authorized-company endpoint. Keep branding, navigation configuration, theme tokens, and local theme/language/last-company preferences centralized in frontend configuration.

**Consequences:** The shell remains easy to revise after first-version review and does not weaken backend authorization. Local preferences are browser conveniences, not durable server-side profile/default-company settings. Business modules, translations, dashboard customization, and accessibility review remain future work.

## AD-010 - Tenant-scoped organization services behind authenticated company context

**Context:** P006 introduces the first mutable customer administration APIs. Browser company selection alone cannot authorize company, branch, or warehouse operations.

**Decision:** Require an authenticated P004 session and an active `UserCompanyAccess` grant for the request `X-Company-ID` before `/organization` operations. Scope every branch and warehouse lookup by that authorized company. Allow only an optional warehouse branch that belongs to the same company. Keep company status/subscription control with Pruvian Technologies and provide profile/status display only to ordinary company-context APIs.

**Consequences:** Object-ID manipulation cannot reveal or change another selected tenant's organization records. P007 can add role-policy checks in the organization service layer without replacing the tenant boundary. Company branding is represented only by an optional logo URL foundation; storage and upload architecture remain deferred.

## AD-011 - Company-scoped P007 administration with additive permissions

**Context:** Company administration needs tenant-safe user, role, permission, and security controls without granting platform access or prematurely introducing operational-module scope rules.

**Decision:** Require an authenticated active `UserCompanyAccess` for `X-Company-ID` and a specific effective company permission for every `/administration` action. Seed eight system-managed company roles and 30 current permissions on demand. Combine permissions additively across active company role assignments. Protect the system-managed Owner role; prevent administrators from assigning permissions they do not hold. Treat branch and warehouse defaults as user preferences only.

**Consequences:** Cross-company administration is rejected, role changes cannot create privilege escalation, and P004 activation/reset/session-revocation capabilities are reused without exposing credentials. Branch/warehouse authorization scope, primary Owner assignment, platform-administration UI, and transactional-module permissions remain deferred.

## AD-012 - Shared company-scoped Party foundation for customers and suppliers

**Context:** Customer and supplier masters need common identity, contact, address, tax, commercial, lifecycle, tenant, and authorization rules without prematurely building CRM or transactions.

**Decision:** Model one company-scoped `Party` as Customer, Supplier, or Both, with extensible primary contact/address child records and locked company-local customer/supplier counters. Require authenticated active-company context and P007 customer/supplier permissions for every `/parties` operation; scope object lookups to the selected company and record party administration audit events. Validate GST/PAN formats and require GSTIN for registered/composition status.

**Consequences:** One business entity can safely serve both roles without duplicate master records, cross-company object IDs return `404`, and browser company selection cannot grant access. Advanced CRM, multiple-contact UI, advanced address management, GST calculations, e-invoice/e-way bill, configurable numbering, and sales/purchase transactions remain deferred.

## AD-013 - Lightweight company-scoped item master

**Decision:** Store Goods and Services in one company-scoped Item model with optional category, controlled UOM code, direct allowed GST-rate foundation, decimal cost/selling prices, optional barcode/image/default warehouse, and per-company `ITEM-0001` sequencing. Opening stock is setup data only; P009 creates no stock ledger or movement.

**Consequences:** Items can support future sales, purchases, inventory, tax, barcode, and pricing work without prematurely implementing those modules. UOM conversion, price lists, GST calculation, scanning/printing, image storage, and configurable numbering remain deferred.

## AD-014 - Purchase documents preserve commercial facts, not ledgers

**Decision:** P010 stores company-scoped PO, GRN, and purchase invoice headers/lines with server-calculated Decimal totals and snapshots of item identity/UOM/description/rate/tax reference. Simple percentage discount and a provisional aggregate tax amount are retained as a commercial foundation. Per-company locked counters create `PO-0001`, `GRN-0001`, and `PI-0001` values.

**Consequences:** GRNs capture accepted/rejected Goods quantities, receipt date, warehouse preference, and source links for P011, but do not post stock. Purchase invoices preserve supplier, dates, due date, and totals for future accounting, but do not post journals, supplier balances, input tax credit, or statutory GST logic.

## AD-015 - Linked purchase lines remain commercial and receipt foundations

**Decision:** Retain PO-line references on GRN lines and add optional PO-line/GRN-line references on purchase-invoice lines. Permit draft editing only; finalizing a GRN validates remaining ordered quantity across prior received GRNs and synchronizes the PO to Partially Received or Received.

**Consequences:** The workflow supports partial receipts and future three-way matching without an inventory ledger. P011 is the only stage authorized to post accepted quantities to stock.

## Provisional Decisions

The initial Owner assignment workflow, future transactional permission catalogue, subscription association, warehouse-to-branch relationship, branch/warehouse authorization scope, administrative policy, application shell/navigation, theme/language preferences, document-layout customization, and future integration/provider choices are intentionally provisional and must be reviewed after first-version testing.
