# Security Guidelines

## Multi-tenant isolation

- Treat company context as a fundamental authorization boundary for every future customer business API.
- Verify the authenticated user has active `UserCompanyAccess` for the selected company before reading or writing its data.
- Do not rely on client-selected company identifiers or frontend hiding as authorization.

## Identity and authentication

- Never store plaintext passwords. Future password authentication must use an adaptive, industry-standard password hash.
- Never store plaintext OTPs. OTPs must be short-lived and protected by the future authentication mechanism.
- Email/password and mobile/OTP methods must resolve to the same `User` identity where both are enabled.
- Do not expose credential hashes or authentication internals in API response schemas.

## Authorization

- Platform administration and customer administration are separate backend concerns. Platform access requires explicit server-side checks.
- Company creators do not automatically receive Owner rights; Accline Services controls the primary Owner assignment.
- Customer administrators may manage other administrators for the first version; review this provisional policy after testing.

## Data protection and operations

- Use UUID primary identifiers for externally addressable foundational entities.
- Enforce foreign keys, uniqueness, checks, and indexes at the database level where supported.
- Keep secrets in environment configuration; do not commit `.env` files or production credentials.
- Apply schema changes exclusively through reviewed Alembic migrations.
- Use separate development, test, and production databases. Automated tests must never target production data.
- Product naming, branding, or frontend navigation must not be treated as an authorization or tenant-isolation mechanism.

## Deferred integrations

- WhatsApp/SMS, GST/e-way bill, QR/barcode, document-layout, and AI-assistant capabilities are not implemented. Future designs must preserve company isolation and keep credentials, sensitive data, and provider access on the server side.
- Provider selection, jurisdiction/compliance scope, AI data access, and retention rules are OPEN; do not assume them in implementation.
