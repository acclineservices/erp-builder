# Active Task

## Task Identifier

P006 - Company, Branch & Warehouse Management

## Status

**COMPLETE** - completed and validated on 2026-09-09. Tenant-scoped company setup, optional branch and warehouse management, same-company warehouse branch validation, lifecycle controls, frontend setup screens, live health/authentication/context checks, frontend production build, and 21 backend tests passed.

No successor implementation task is active. P007 is not started.

## Scope

Build the first authenticated ERP administration functionality: company setup, optional branches, optional warehouses, tenant-safe organization APIs, and setup screens without introducing P007 role management or business modules.

## Constraints

- Preserve P003 organization identity, P004 authentication/session/platform boundary, and P005 shell.
- Enforce active UserCompanyAccess on every organization API; do not rely on browser filtering or enable cross-company branch association.
- Do not implement P007 RBAC management, billing, document storage, or business modules.

## Definition of Done

- Company profile data, setup progress, optional GST/contact/address fields, and status display are available in the selected authorized context.
- Branches and warehouses support creation, editing, viewing, activation/deactivation, empty states, and no fake default operating locations.
- Warehouse branch links are validated to the same company, and tenant-isolation/lifecycle/zero-location tests pass.
- Documentation records P006 completion while P007 remains not started.
