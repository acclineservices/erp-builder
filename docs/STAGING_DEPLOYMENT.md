# Pruvian staging deployment preparation

P010.1 prepares the Pruvian application for an online Render staging deployment. It does **not** create Render services and does not mark staging deployment complete. P011 has not started.

## Brand and domains

- Company: **Pruvian Technologies**
- Product: **Pruvian**
- Tagline: **Run Better. Grow Smarter.**
- Description: **Cloud Accounting & Business Management Platform**
- Marketing site: `pruviantechnologies.com`
- Staging application: `staging.pruviantechnologies.com`
- Future production application/API: `app.pruviantechnologies.com` and `api.pruviantechnologies.com`

`Pruvian ERP` and `pruvian-erp-*` remain appropriate internal development and infrastructure names.

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

## Go-live checklist

1. Create the backend Web Service with the settings above and connect its private database URL as `DATABASE_URL`.
2. After the first backend deployment passes `/health` and `/health/database`, create the frontend Static Site with the generated backend URL in `VITE_API_BASE_URL`.
3. Add the generated frontend URL and `https://staging.pruviantechnologies.com` to `BACKEND_CORS_ORIGINS`, then redeploy the backend.
4. Add the frontend rewrite rule and verify direct-route refreshes.
5. Connect `staging.pruviantechnologies.com` to the Static Site. After its HTTPS certificate is active, rebuild the frontend with its intended API URL and confirm login, logout, cookies, CORS, `/health`, and `/health/database` online.
6. Do not treat staging as complete until the founder has tested the connected deployment online.
