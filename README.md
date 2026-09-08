# ERP Builder

## Project Vision

ERP Builder is the engineering foundation for a long-term, commercial SaaS ERP platform. It provides a minimal web application plus a modular Identity & Organization database foundation so the product can grow through deliberate, secure decisions.

## Repository Structure

```text
ERP-Builder/
├── AI_CONTEXT/       # Durable product and engineering context for collaborators
├── AI_PLAYBOOK/      # Reusable work templates and decision history
├── backend/          # FastAPI API application, SQLAlchemy models, Alembic, and tests
├── frontend/         # React + Vite + Tailwind application
├── database/         # Future database assets (no ERP business tables)
├── docs/             # Product and technical documentation
├── scripts/          # Development and maintenance automation
├── docker/           # Development container definitions
└── .github/          # Future GitHub-specific repository assets
```

## Local Development

### 1. Configure environment values

Copy `.env.example` to `.env`. The supplied PostgreSQL values are development-only placeholders; replace the password for local use if needed. You may either set the individual `POSTGRES_*` values or set a complete `DATABASE_URL`.

```powershell
Copy-Item .env.example .env
```

### 2. Start PostgreSQL through Docker

Docker Desktop must be running. From the repository root:

```powershell
docker compose up -d database
```

This exposes PostgreSQL at `localhost:5432` by default. PostgreSQL does not need to be installed directly on Windows.

### 3. Set up the backend and apply migrations

From `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

To create a future migration after changing models:

```powershell
alembic revision --autogenerate -m "description"
```

To roll back one revision:

```powershell
alembic downgrade -1
```

The API is available at `http://localhost:8000`. `GET /health` reports API process availability; `GET /health/database` separately checks PostgreSQL connectivity.

### 4. Start the frontend

In a separate terminal, from `frontend/`:

```powershell
npm install
npm run dev
```

The frontend is available at `http://localhost:5173`.

### Docker Compose

To run the complete development stack (PostgreSQL, backend, and frontend):

```powershell
docker compose up --build
```

The backend container runs `alembic upgrade head` before starting FastAPI. The supplied `.env.example` values are development-only placeholders.

### Validation

Run backend tests from `backend/`:

```powershell
.\.venv\Scripts\python -m pytest
```

Build the frontend from `frontend/`:

```powershell
npm run build
```

## Database Foundation

The P003 database foundation uses PostgreSQL, SQLAlchemy 2.x, and Alembic. Users are independent of companies and can have explicit active access to multiple companies. Companies are the future business-data isolation boundary. Branches and warehouses each belong to a company but are optional. RBAC structures support platform and company roles without implementing any login, authorization middleware, billing, or ERP business module.

## Development Workflow

1. Review the relevant documents in `AI_CONTEXT/` before beginning work.
2. Define the scope and record material decisions in `AI_CONTEXT/12_DECISION_LOG.md`.
3. Implement only the work authorized by the active engineering task.
4. Keep changes modular, documented, and proportionate to the requirement.
5. Update project context and next steps when a task changes the shared understanding.

## Folder Overview

The root folders separate durable context, implementation layers, documentation, automation, and infrastructure concerns. P002 introduced the runnable web application foundation; P003 adds the identity/organization database infrastructure only. Product modules remain future work.

## Contribution Philosophy

Prefer clear boundaries, small purposeful changes, and maintainable defaults. Avoid speculative abstractions, premature dependencies, and business assumptions that have not been approved.

## Repository Conventions

### AI_CONTEXT

`AI_CONTEXT/` is the durable source of shared product, engineering, architecture, and task context. Review and update it when approved work changes the repository's shared understanding.

### AI_PLAYBOOK

`AI_PLAYBOOK/` contains reusable templates and standards that support consistent collaboration, planning, and review.

### Engineering Tasks

Engineering tasks define the authorized scope of work. Changes should remain within that scope, and completion should include proportionate verification and a clear handoff.

### Documentation Philosophy

Documentation should be purposeful, current, and grounded in approved decisions. Prefer concise records that clarify ownership, rationale, and next actions over speculative detail.
