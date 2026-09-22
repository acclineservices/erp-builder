# Decision Log

## Purpose

Provide a chronological record of material product and engineering decisions.

## Placeholder Sections

- Decision template
- Decision entries
- Superseded decisions
- Open decisions

## 2026-09-22 - P010.1: finalized Pruvian brand and staging deployment preparation

- **Decision:** Customer-facing company and product names are Pruvian Technologies and Pruvian. The tagline is *Run Better. Grow Smarter.* and the description is *Cloud Accounting & Business Management Platform*. `Pruvian ERP` remains the internal project name; `pruvian-erp-*` remains valid infrastructure naming.
- **Decision:** Render staging receives its PostgreSQL connection only through secret `DATABASE_URL`; standard `postgresql://` URLs are normalized to the installed psycopg 3 driver. Existing local `POSTGRES_*` Docker configuration remains supported.
- **Decision:** Browser CORS origins and session-cookie security attributes are environment-driven. Credentialed CORS cannot use a wildcard origin. HTTPS staging uses secure cookies; SameSite and cookie domain remain explicit deployment choices.
- **Decision:** Staging service creation and online testing are external manual work. P010.1 documents the configuration but does not claim an online staging deployment is complete.
