# Security Guidelines

## Multi-tenant isolation

- Treat company context as a fundamental authorization boundary for every future customer business API.
- Verify the authenticated user has active `UserCompanyAccess` for the selected company before reading or writing its data.
- Do not rely on client-selected company identifiers or frontend hiding as authorization.
- P008 Party requests must also require the appropriate P007 customer/supplier permission and scope every Party lookup to the authorized company; return `404` for a Party outside that company context.
- P009 item/category requests require active company context plus P007 item permission; codes, barcodes, categories, and optional warehouse references are validated within that company.

## Identity and authentication

- Never store plaintext passwords; P004 uses bcrypt password hashes.
- Never store plaintext OTPs; P004 stores bcrypt OTP hashes, applies expiry and attempt limits, and does not expose them in normal API responses.
- P004 stores only SHA-256 digests for opaque sessions and single-use activation, verification, and recovery tokens.
- Email/password and mobile/OTP methods resolve to the same `User` identity where both are enabled and verified.
- Do not expose credential hashes, tokens, OTPs, or authentication internals in API response schemas. Use generic login and recovery responses.

## Authorization

- Platform administration and customer administration are separate backend concerns. Platform access requires explicit server-side checks.
- Company creators do not automatically receive Owner rights; Accline Services controls the primary Owner assignment.
- P007 administration requires both active company access and the relevant effective company permission; never treat company selection or UI hiding as authorization.
- Effective company permissions are additive across role assignments. Administrators may not grant permissions they do not hold, and system-managed Owner access may not be mutated through ordinary company administration.
- Customer/supplier create, edit, view, and lifecycle actions use the current P007 permission catalogue and write audit events; frontend navigation and company switching do not replace these checks.
- Branch/warehouse defaults are preferences, not authorization scope. Branch-level and warehouse-level authorization remain deferred.
- Customer administrators may manage other administrators only within the permissions they hold; review this provisional policy after testing.

## Data protection and operations

- Use UUID primary identifiers for externally addressable foundational entities.
- Enforce foreign keys, uniqueness, checks, and indexes at the database level where supported.
- Treat GSTIN, PAN, business contact details, and commercial master data as company business data. Validate structured API errors into safe user-facing messages; never expose stack traces or persistence internals.
- Keep secrets in environment configuration; do not commit `.env` files or production credentials.
- Apply schema changes exclusively through reviewed Alembic migrations.
- Use separate development, test, and production databases. Automated tests must never target production data.
- Use server-side revocation for logout and password reset; treat platform-admin sessions as a separate cookie and route boundary.
- The development notification provider is in-memory only. Production provider credentials and delivery controls must remain server-side and outside source control.
- Product naming, branding, or frontend navigation must not be treated as an authorization or tenant-isolation mechanism.

## Deferred integrations

- WhatsApp/SMS, GST/e-way bill, QR/barcode, document-layout, and AI-assistant capabilities are not implemented. Future designs must preserve company isolation and keep credentials, sensitive data, and provider access on the server side.
- Provider selection, jurisdiction/compliance scope, AI data access, and retention rules are OPEN; do not assume them in implementation.
