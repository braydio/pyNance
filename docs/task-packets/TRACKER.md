# Task Packet Tracker

Live execution ledger. Update this file whenever packet status, blocker, dependency, owner/workstream, or lifecycle location changes.

Controlled statuses and lifecycle rules are defined in [README.md](README.md).

| Packet ID | Title | Status | Priority | Depends on | Target | Last updated | Packet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TP-20261007-002 | UI Hierarchy Foundation + App Shell | Ready | High | TP-20261007-001 | main | 2026-10-07 | [packet](active/TP-20261007-002-ui-hierarchy-foundation-app-shell.md) |
| TP-20261007-003 | Dashboard Decision-First Recomposition | Ready | High | TP-20261007-001, TP-20261007-002 | main | 2026-10-07 | [packet](active/TP-20261007-003-dashboard-decision-first-recomposition.md) |
| TP-20261007-004 | Transactions Action Workbench | Ready | High | TP-20261007-002 | main | 2026-10-07 | [packet](active/TP-20261007-004-transactions-action-workbench.md) |
| TP-20261007-005 | Accounts Portfolio + Connection Hierarchy | Ready | High | TP-20261007-002 | main | 2026-10-07 | [packet](active/TP-20261007-005-accounts-portfolio-connection-hierarchy.md) |
| TP-20261007-006 | Forecast Explainable Decision Surface | Ready | Normal | TP-20261007-002 | main | 2026-10-07 | [packet](active/TP-20261007-006-forecast-explainable-decision-surface.md) |
| TP-20261007-007 | Planning Workflow Reauthor | Ready | High | TP-20261007-002 | main | 2026-10-07 | [packet](active/TP-20261007-007-planning-workflow-reauthor.md) |
| TP-20261007-008 | Investments Portfolio Hierarchy | Ready | Normal | TP-20261007-002 | main | 2026-10-07 | [packet](active/TP-20261007-008-investments-portfolio-hierarchy.md) |
| TP-20261007-009 | Cross-App Readability + Responsive + Accessibility Closure | Ready | Normal | TP-20261007-003, 004, 005, 006, 007, 008 | main | 2026-10-07 | [packet](active/TP-20261007-009-cross-app-readability-responsive-accessibility-closure.md) |
| TP-20261007-001 | Local Schema Head Activation + Safe-to-Spend Migration Guard | Blocked | High | TP-20261002-001 | main | 2026-10-08 | [packet](active/TP-20261007-001-local-schema-head-activation.md) |
| TP-20261002-001 | Safe-to-Spend Reliability + Correct Cashflow Semantics | Complete | High | None | main | 2026-10-07 | [packet](completed/TP-20261002-001-safe-to-spend-reliability.md) |
| TP-20261001-001 | Plaid Item Connection Health + Reconnect UI | Complete | Normal | None | main | 2026-10-08 | [packet](completed/TP-20261001-001-plaid-connection-health-reconnect.md) |

## Execution notes

- Start with the highest-priority Ready packet unless the user or an explicit dependency says otherwise.
- Change `Ready` to `In Progress` when implementation actually begins.
- A `Blocked` row must include a concise blocker below this table and the concrete condition for resuming.
- `Complete` packets move to `completed/`; `Superseded` and `Cancelled` packets move to `archived/`.
- Keep completed/archived rows in this tracker for history, but active work should remain visually easy to identify.

## Blockers

- **TP-20261007-001:** The configured database target reports `ENV=production` (`pynance:public`), current revision `e6a9c2f4b8d1`, while repository head is `f84c6e2a91b7`; `planned_bills.frequency`, `origin`, and `account_id` are absent. Do not run the upgrade against this target. Resume after configuring the intended local database with `ENV=development` or receiving explicit production migration direction.
