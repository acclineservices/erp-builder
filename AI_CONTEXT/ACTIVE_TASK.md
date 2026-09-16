# Active Task

## Task Identifier

P007 - User, Role & Permission Management

## Status

**COMPLETE** - completed and validated on 2026-09-16. Company-scoped user and role administration, invitation/activation integration, granular permissions, safe security actions, audit events, tenant isolation, frontend Users & Roles UI, live API checks, frontend production build, and 26 backend tests passed.

No successor implementation task is active. P008 has not started.

## Scope

Build company-scoped user management and RBAC administration without introducing transactional ERP modules or platform-administration UI.

## Constraints

- Preserve active UserCompanyAccess as the tenant boundary and enforce required P007 permissions server-side.
- Keep the primary Owner workflow under Accline Services control; prevent ordinary owner mutation and administrator privilege escalation.
- Keep branch/warehouse authorization scope, platform-administration UI, billing, document storage, and business modules deferred.

## Definition of Done

- Users can be invited, activated through P004, assigned multiple company roles, made active/inactive for a company, and given same-company default branch/warehouse preferences.
- Eight fixed roles, custom roles, cloning, 30 current permissions, additive effective permissions, Owner protection, privilege-escalation prevention, force logout, reset/activation initiation, audit events, and tenant isolation are implemented.
- Users, Roles, Permissions, and Security administration are usable in `/app/users`; validation records Alembic `d07a3e1b4f91` and 26 backend tests passed.
