# Active Task

## Task Identifier

P008 - Customer & Supplier Management

## Status

**COMPLETE** - completed and validated on 2026-09-17. Shared Customer/Supplier/Both Party management, contact/address foundations, generated codes, GST/PAN validation, commercial fields, lifecycle/search, P007 permission enforcement, tenant isolation, audit events, readable API errors, frontend Customers/Suppliers UI, live API checks, and frontend production build passed.

No successor implementation task is active. P009 has not started.

## Scope

Build company-scoped customer/supplier master management without introducing advanced CRM, transactional ERP modules, or P009 functionality.

## Constraints

- Preserve active UserCompanyAccess as the tenant boundary and enforce required P007 customer/supplier permissions server-side.
- Keep GST calculations, e-invoice/e-way bill, configurable numbering, sales/purchase transactions, and advanced CRM/contact/address management deferred.
- Do not start P009.

## Definition of Done

- Customer, Supplier, and Both Party records support validated contact/address, tax, and commercial foundations; company-local codes, lifecycle, search/filter, audit, RBAC, and tenant isolation are enforced.
- Customers and Suppliers are usable at `/app/customers` and `/app/suppliers`, reload with company switching, and format structured API validation errors safely.
- Validation records Alembic `e008a1b2c3d4`, 29 backend tests, 3 P008 tests, 18 prior-module regression tests, frontend build, live create/edit/lifecycle checks, and founder visual review.
