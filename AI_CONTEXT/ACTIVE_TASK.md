# Active Task

## Task Identifier

P004 - Authentication Foundation

## Status

**COMPLETE** - completed and validated on 2026-09-09. Migration `b71f4e9c2a10`, live PostgreSQL/backend checks, 18 backend tests (including 10 authentication tests), and the frontend production build passed.

No successor implementation task is active. P005 is not started.

## Scope

Implement the authentication foundation: email/password and mobile OTP login, activation and verification, password recovery, server-side sessions, temporary failed-login protection, platform-admin boundary, authenticated user/company context, tests, and documentation handoff.

## Constraints

- Preserve P002/P003 foundations and existing repository boundaries.
- Do not implement user/company administration workflows, paid production email/SMS/WhatsApp providers, billing, subscriptions, or ERP business modules.
- Use the development notification-provider abstraction and keep secrets outside source control.

## Definition of Done

- P004 authentication flows, account states, session behavior, platform boundary, and company-list restriction are implemented and tested.
- Migration `b71f4e9c2a10` is applied and validated.
- No plaintext passwords, OTPs, or tokens are persisted or exposed by normal API responses.
- Documentation and developer instructions describe the delivered architecture and validation state.
