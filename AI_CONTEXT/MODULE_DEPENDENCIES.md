# Module Dependencies

## Shared Platform Capabilities

| Capability | Depends on | Constraints |
| --- | --- | --- |
| Identity foundation | PostgreSQL, SQLAlchemy, Alembic | A user exists independently of any company. |
| Authentication foundation | User, AuthenticationMethod, Session, AuthToken, OtpChallenge | Email/password and mobile/OTP map to one user; persist only password/OTP/token digests and require active, verified methods. |
| Authenticated company context | Session, UserCompanyAccess, Company | P004 lists only active accessible companies; future customer APIs must validate active access to the selected company. |
| Company administration RBAC | Session, UserCompanyAccess, Role, Permission, RoleAssignment, UserManagementAuditEvent | P007 requires active company access and effective company permission; 8 fixed roles and 30 current permissions are seeded on demand, while custom roles remain company-scoped. |
| Branch/warehouse-aware modules (future) | Company, optional Branch/Warehouse | Must work for companies with zero branches and zero warehouses. |
| Application shell and navigation foundation | P004 session context, authorized company list, navigation configuration | P005 protects app routes, renders responsive shell/navigation placeholders, and never grants company access from browser state. |
| Organization management | P004 session, UserCompanyAccess, Company, optional Branch/Warehouse | P006 requires active access to `X-Company-ID`, scopes queries to that company, and permits warehouse `branch_id` only when it belongs to the same company. Branch/warehouse authorization scope remains deferred. |
| Customer and supplier management | P004 session, UserCompanyAccess, P007 Role/Permission/RoleAssignment, Party, PartyContact, PartyAddress, PartyCodeSequence | P008 requires active `X-Company-ID` access and the relevant customer/supplier permission, scopes all Party reads/writes by company, and records audit events. Contacts/addresses are foundations, not advanced CRM. |
| Item master management | P004 session, UserCompanyAccess, P006 optional Warehouse, P007 RBAC/audit | P009 scopes categories/items/codes/barcodes to company and validates optional warehouse ownership; default warehouse is a convenience, not security scope. |
| Branding, themes, languages, and document layouts (future) | Application shell | Customization requirements are planned; scope and persistence model are OPEN. |
| WhatsApp/SMS, GST/e-way bill, QR/barcode, and AI capabilities (future) | Company context, authorization, future business/document modules | Provider, jurisdiction, payload, data-access, and sequencing decisions are OPEN. |

## Dependency Constraints

- Sales, purchase, inventory, finance, accounting, documents, reports, and AI modules are not implemented and must not be introduced without explicit company scoping.
- The Accline Services administration area must use the P004 platform-session boundary and future platform-level access checks, independent of frontend visibility.
- P005 company selection is a client presentation preference only; P006 demonstrates that every customer API must independently validate active UserCompanyAccess and scope all record queries to the selected company.
- P007 administration adds required company permissions after the active-company check; it does not make branch/warehouse defaults into authorization boundaries.
- P008 applies the same active-company and permission boundary to customer/supplier masters. Customer/supplier codes and GSTIN uniqueness are company-local; cross-company Party IDs must not reveal records.
- Subscription/billing capabilities may later relate to `Company`; P003 intentionally creates no billing schema or pricing policy.
- Product naming and branding are not tenant or architecture boundaries; ERP Builder is the current name and may change later.
