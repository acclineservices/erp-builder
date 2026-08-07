# ERP Builder

## Project Vision

ERP Builder is the engineering foundation for a long-term, commercial SaaS ERP platform. The repository is intentionally established before application implementation so the product can grow through deliberate, modular decisions.

## Repository Structure

```text
ERP-Builder/
├── AI_CONTEXT/       # Durable product and engineering context for collaborators
├── AI_PLAYBOOK/      # Reusable work templates and decision history
├── backend/          # Future backend application boundaries
├── frontend/         # Future React application boundaries
├── database/         # Future database assets
├── docs/             # Product and technical documentation
├── scripts/          # Development and maintenance automation
├── docker/           # Future container-related assets
└── .github/          # Future GitHub-specific repository assets
```

## Development Workflow

1. Review the relevant documents in `AI_CONTEXT/` before beginning work.
2. Define the scope and record material decisions in `AI_CONTEXT/12_DECISION_LOG.md`.
3. Implement only the work authorized by the active engineering task.
4. Keep changes modular, documented, and proportionate to the requirement.
5. Update project context and next steps when a task changes the shared understanding.

## Folder Overview

The root folders separate durable context, implementation layers, documentation, automation, and infrastructure concerns. Application code and product modules will be added only through future engineering tasks.

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
