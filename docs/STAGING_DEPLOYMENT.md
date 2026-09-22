# Pruvian online staging deployment

**Status: COMPLETE.** P010.1 staging is live and founder-tested. P011 has not started.

## Brand and domains

- Company: **Pruvian Technologies**
- Product: **Pruvian**
- Tagline: **Run Better. Grow Smarter.**
- Description: **Cloud Accounting & Business Management Platform**
- Marketing site: `pruviantechnologies.com`
- Staging application: `staging.pruviantechnologies.com`
- Future production application/API: `app.pruviantechnologies.com` and `api.pruviantechnologies.com`

`Pruvian ERP` and `pruvian-erp-*` remain appropriate internal development and infrastructure names.

## Live staging

| Component | Live address or resource |
| --- | --- |
| Staging application | `https://staging.pruviantechnologies.com` |
| Staging API | `https://api-staging.pruviantechnologies.com` |
| API health | `https://api-staging.pruviantechnologies.com/health` |
| Database health | `https://api-staging.pruviantechnologies.com/health/database` |
| Render frontend | `pruvian-staging` |
| Render backend | `pruvian-erp-staging-api` |
| Render PostgreSQL | `pruvian-erp-staging-db` (PostgreSQL 16, Singapore) |

## Domain architecture

| Domain | Purpose |
| --- | --- |
| `pruviantechnologies.com` | Future marketing and company website |
| `staging.pruviantechnologies.com` | Live staging Pruvian application |
| `api-staging.pruviantechnologies.com` | Live staging API |
| `app.pruviantechnologies.com` | Future production application |
| `api.pruviantechnologies.com` | Future production API |

## Backend Render Web Service

Create a Python Web Service in Singapore from `main` with these values:

| Setting | Value |
| --- | --- |
| Service name | `pruvian-erp-staging-api` |
| Root Directory | `backend` |
| Build Command | `pip install .` |
| Start Command | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

Do not set `PORT`; Render provides it. The command migrates the fresh staging database to the current preserved Alembic head before Uvicorn starts. A failed migration fails the deployment instead of serving an incompatible schema.

Set these backend environment variables in Render. Add the database connection using the database service's private `DATABASE_URL` value in Render; it is a secret and must never be copied to this repository.

| Variable | Staging value |
| --- | --- |
| `APP_ENV` | `staging` |
| `DATABASE_URL` | Render PostgreSQL private connection string (secret) |
| `BACKEND_CORS_ORIGINS` | comma-separated frontend origins, initially the generated Static Site URL and `https://staging.pruviantechnologies.com` |
| `AUTH_COOKIE_SECURE` | `true` |
| `AUTH_COOKIE_SAMESITE` | `none` initially for distinct generated Render frontend/API hosts; after both custom domains use `*.pruviantechnologies.com`, `lax` is the preferred same-site setting |
| `AUTH_COOKIE_DOMAIN` | leave blank for the safer host-only API cookie; set only after an intentional subdomain-sharing design |

`BACKEND_CORS_ORIGINS` must contain explicit origins, never `*`, because browser requests include session cookies. If `AUTH_COOKIE_SAMESITE=none`, `AUTH_COOKIE_SECURE=true` is required.

## Frontend Render Static Site

Create a Static Site from `main` with these values:

| Setting | Value |
| --- | --- |
| Service name | `pruvian-erp-staging-web` |
| Root Directory | `frontend` |
| Build Command | `npm ci && npm run build` |
| Publish Directory | `dist` |
| Build environment variable | `VITE_API_BASE_URL=https://<generated-backend-service>.onrender.com` |

`VITE_API_BASE_URL` is compiled into the static Vite build. Set it before each frontend staging build, first to the generated backend HTTPS URL, then to `https://api.pruviantechnologies.com` when that custom domain is connected. Local development continues to default to `http://localhost:8000`.

Add a Render Static Site **Rewrite** rule, not a redirect:

| Source | Destination | Action |
| --- | --- | --- |
| `/*` | `/index.html` | Rewrite |

This lets Vite's browser-history application handle direct visits and refreshes for `/auth`, `/app/dashboard`, `/app/customers`, `/app/suppliers`, `/app/items`, and `/app/purchases`. Static assets still take precedence on Render.

## Confirmed founder validation

The founder confirmed custom frontend/backend domains, HTTPS, login/logout cycles, authenticated dashboard access, session cookies, CORS, direct SPA-route refreshes, laptop use, phone/mobile-data use, and operation independent of the founder's local PC.

## One-time staging bootstrap — completed

The initial company and Owner provisioning was completed through the guarded bootstrap command. The temporary bootstrap environment variables have been removed from Render. Do not add them back or place their values in this repository or frontend build configuration.

- `STAGING_BOOTSTRAP_EMAIL`
- `STAGING_BOOTSTRAP_MOBILE`
- `STAGING_BOOTSTRAP_PASSWORD`
- `STAGING_BOOTSTRAP_COMPANY_NAME`

If a future, explicitly authorized staging reset requires the command, it refuses to run unless `APP_ENV=staging`. Its temporary Start Command is:

```sh
alembic upgrade head && python -m app.scripts.bootstrap_staging
```

The process exits after provisioning; restore the normal Start Command and redeploy:

```sh
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The command is idempotent: it reuses the matching user/company, restores active and verified state, calls the existing P007 catalogue seeding, and adds the Owner assignment only when absent. It creates no HTTP endpoint, emits no password/hash/token values, and does not grant platform-admin access.

## Current security and operations

- The staging API runs with `APP_ENV=staging`, `AUTH_COOKIE_SECURE=true`, `AUTH_COOKIE_SAMESITE=lax`, and `BACKEND_CORS_ORIGINS=https://staging.pruviantechnologies.com`.
- The cloud staging PostgreSQL database is separate from local Docker PostgreSQL development. Local Docker development remains supported.
- The backend uses Render private-network database connectivity. Public/external staging database access is restricted.
- Database connection strings remain Render secrets and are never documented or committed.
- Render Free Web Services may sleep after inactivity and have a cold-start delay. This is acceptable for the current staging environment.

## Future production-readiness work

- Define backup and retention policies.
- Add monitoring and operational alerting.
- Establish production infrastructure separation from staging.
- Complete a production deployment and security review.
- Run a dedicated UI/UX refinement phase before design approval.

## Future UI/UX refinement phase

The current UI is functional but not design-approved. A dedicated, separately authorized UI/UX phase must cover the Pruvian brand palette, typography, alignment, spacing, hierarchy, sidebar/header, dashboard, forms, tables/lists, responsive/mobile behavior, component consistency, light/dark themes, and overall visual polish. This checkpoint makes no visual redesign.
