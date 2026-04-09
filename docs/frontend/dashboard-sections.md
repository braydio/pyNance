# Dashboard Sections UI Contracts

_Last updated: 2026-04-08_

## Scope

This document tracks shared UI contracts for dashboard section shells:

- `frontend/src/components/dashboard/AccountsSection.vue`
- `frontend/src/components/dashboard/TransactionsSection.vue`
- `frontend/src/components/dashboard/CategoryBreakdownSection.vue`

## Base Primitive Adoption

These sections now consume `frontend/src/components/base/` primitives rather than duplicating control and panel geometry:

- `BasePanel` for section shell surface/border/radius behavior
- `BaseButton` for close actions and category/merchant mode controls

This centralizes angular spacing, border treatment, and focus-ring behavior in base primitives.
