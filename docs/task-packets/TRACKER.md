# Task Packet Tracker

Live execution ledger. Update this file whenever packet status, blocker, dependency, owner/workstream, or lifecycle location changes.

Controlled statuses and lifecycle rules are defined in [README.md](README.md).

| Packet ID | Title | Status | Priority | Depends on | Target | Last updated | Packet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TP-20261002-001 | Safe-to-Spend Reliability + Correct Cashflow Semantics | Ready | High | None | main | 2026-10-03 | [packet](active/TP-20261002-001-safe-to-spend-reliability.md) |
| TP-20261001-001 | Plaid Item Connection Health + Reconnect UI | Ready | Normal | None | main | 2026-10-03 | [packet](active/TP-20261001-001-plaid-connection-health-reconnect.md) |

## Execution notes

- Start with the highest-priority Ready packet unless the user or an explicit dependency says otherwise.
- Change `Ready` to `In Progress` when implementation actually begins.
- A `Blocked` row must include a concise blocker below this table and the concrete condition for resuming.
- `Complete` packets move to `completed/`; `Superseded` and `Cancelled` packets move to `archived/`.
- Keep completed/archived rows in this tracker for history, but active work should remain visually easy to identify.

## Blockers

None currently recorded.
