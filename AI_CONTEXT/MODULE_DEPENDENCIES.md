# Module Dependencies

## Shared Platform Capabilities

| Capability | Depends on | Constraints |
| --- | --- | --- |
| Identity foundation | PostgreSQL, SQLAlchemy, Alembic | A user exists independently of any company. |
| Authentication (future) | User, AuthenticationMethod | Email/password and mobile/OTP must map to the same user; never persist plaintext passwords or OTPs. |
| Company context | UserCompanyAccess, Company | Future customer APIs must validate active access to the selected company. |
| RBAC (future enforcement) | Role, Permission, RoleAssignment | Platform roles and company roles require server-side enforcement. |
| Branch/warehouse-aware modules (future) | Company, optional Branch/Warehouse | Must work for companies with zero branches and zero warehouses. |

## Dependency Constraints

- Sales, purchase, inventory, finance, accounting, documents, reports, and AI modules are not implemented and must not be introduced without explicit company scoping.
- The Accline Services administration area must use platform-level access checks, independent of frontend visibility.
- Subscription/billing capabilities may later relate to `Company`; P003 intentionally creates no billing schema or pricing policy.
