# Task Packet Tracker

Live execution ledger. Update this file whenever packet status, blocker, dependency, owner/workstream, or lifecycle location changes.

Controlled statuses and lifecycle rules are defined in [README.md](README.md).

| Packet ID | Title | Status | Priority | Depends on | Target | Last updated | Packet |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TP-20261019-004 | Dashboard Glanceability, Panel Hierarchy and Overflow | Ready | P1 | TP-20261019-003 (table chrome baseline) | main | 2026-10-19 | [packet](active/TP-20261019-004-dashboard-glanceability-and-surface-hierarchy.md) |
| TP-20261019-005 | Investment, Planning and Recurring Ledger Summaries | Ready | P2 | TP-20261019-003 and TP-20261019-004 | main | 2026-10-19 | [packet](active/TP-20261019-005-domain-ledger-breakdowns-and-qa.md) |
| TP-20261016-001 | Forecast Transaction Sign Contract and Reconciliation | Complete | P0 | None | main | 2026-10-17 | [packet](completed/TP-20261016-001-forecast-transaction-sign-contract.md) |
| TP-20261016-002 | Recurring Stream Persistence, Account Scope and Legacy API Repair | Complete | P0 | None | main | 2026-10-17 | [packet](completed/TP-20261016-002-recurring-schema-api-integrity.md) |
| TP-20261016-003 | Transfer Matching Security, Scope, Evidence and Review | Complete | P0 | TP-20261016-001 | main | 2026-10-17 | [packet](completed/TP-20261016-003-transfer-review-scan-safety.md) |
| TP-20261016-004 | Unify Recurrence Detector with Forecast Pattern Evidence | Complete | P1 | TP-20261016-001, TP-20261016-002 | main | 2026-10-17 | [packet](completed/TP-20261016-004-recurring-pattern-detection-unified.md) |
| TP-20261016-005 | Recurring Review API, Durable Decisions and Usable UI | Complete | P1 | TP-20261016-002, TP-20261016-004 | main | 2026-10-17 | [packet](completed/TP-20261016-005-recurring-review-api-workflow.md) |
| TP-20261016-006 | Forecast Debt Payments vs Purchases: Settlement-Aware Cash Ledger | Complete | P1 | TP-20261016-001, TP-20261016-003, TP-20261016-005 | main | 2026-10-17 | [packet](completed/TP-20261016-006-forecast-debt-settlement-cashflows.md) |
| TP-20261016-007 | Accounts Classification and Financial Coverage Integrity | Complete | P0 | None | main | 2026-10-17 | [packet](completed/TP-20261016-007-account-classification-coverage-truth.md) |
| TP-20261016-008 | Accounts Overview Hierarchy, Width, Period and Connection Styling | Complete | P2 | TP-20261016-007 | main | 2026-10-17 | [packet](completed/TP-20261016-008-accounts-command-center-hierarchy.md) |
| TP-20261016-009 | Transactions Insights, Review Queue, Sorting and Filtering | Complete | P1 | TP-20261016-001, TP-20261016-003, TP-20261016-005 | main | 2026-10-17 | [packet](completed/TP-20261016-009-transactions-insights-review-workbench.md) |
| TP-20261016-010 | Forecast Driver Groups, Currency Formatting and Debt Coverage Clarity | Complete | P1 | TP-20261016-006 | main | 2026-10-17 | [packet](completed/TP-20261016-010-forecast-explained-breakdown-currency.md) |
| TP-20261016-011 | Cross-Page Financial Truth and Interaction Regression Gate | Complete | P1 | TP-20261016-001 through TP-20261016-010 | main | 2026-10-18 | [packet](completed/TP-20261016-011-end-to-end-financial-ux-regression.md) |
| TP-20261017-001 | Project Recurring Cash Obligations into Safe-to-Spend | Complete | P0 | TP-20261016-001, TP-20261016-002, TP-20261016-004, TP-20261016-005, TP-20261017-006, TP-20261017-007 | main | 2026-10-18 | [packet](completed/TP-20261017-001-recurring-safe-to-spend-obligation-projection.md) |
| TP-20261017-002 | Explain Recurring Reserves and Missing-Coverage Reasons in Safe-to-Spend | Complete | P1 | TP-20261017-001, TP-20261017-007, TP-20261016-005 | main | 2026-10-18 | [packet](completed/TP-20261017-002-safe-to-spend-obligation-explanation-ui.md) |
| TP-20261017-003 | Classify Economic Flows Before Daily Net Aggregation | Complete | P0 | TP-20261016-001, TP-20261016-003 | main | 2026-10-17 | [packet](completed/TP-20261017-003-economic-flow-classification-dashboard.md) |
| TP-20261017-004 | Reconcile Daily Net Chart and Transaction Modal | Complete | P1 | TP-20261017-003, TP-20261016-009 | main | 2026-10-18 | [packet](completed/TP-20261017-004-daily-net-modal-reconciliation.md) |
| TP-20261017-005 | Payday Detection with Sources, Confidence and Read-only Evidence | Complete | P0 | TP-20261016-001, TP-20261016-002, TP-20261016-004, TP-20261016-005, TP-20261017-003 | main | 2026-10-17 | [packet](completed/TP-20261017-005-payday-inference-evidence.md) |
| TP-20261017-006 | Correct Safe-to-Spend Cash Basis and Remove Double Charges | Complete | P0 | TP-20261016-001, TP-20261016-003, TP-20261016-007, TP-20261017-003 | main | 2026-10-17 | [packet](completed/TP-20261017-006-safe-spend-cash-basis-reconciliation.md) |
| TP-20261017-007 | Safe-to-Spend Protection Horizon and Headline Truth | Complete | P0 | TP-20261017-005, TP-20261017-006 | main | 2026-10-17 | [packet](completed/TP-20261017-007-safe-spend-window-and-display-contract.md) |
| TP-20261019-001 | Daily Net Period Buckets, Readability and Reconciliation | Complete | P1 | None (build on completed TP-20261017-003/004) | main | 2026-10-19 | [packet](completed/TP-20261019-001-daily-net-period-buckets-visual-truth.md) |
| TP-20261019-002 | Filter-Aware Financial Table Totals and Scope Contract | Complete | P0 | None; use completed economic-flow TP-20261017-003/004 | main | 2026-10-19 | [packet](completed/TP-20261019-002-filter-aware-table-summary-contract.md) |
| TP-20261019-003 | Professional Table System, Totals and Drilldowns | Complete | P1 | TP-20261019-002 | main | 2026-10-19 | [packet](completed/TP-20261019-003-professional-tables-and-total-bars.md) |
| TP-20261014-010 | Theme Contrast and Typography | Complete | High | None | main | 2026-10-14 | [packet](completed/TP-20261014-010-theme-contrast-typography.md) |
| TP-20261014-011 | Shared Fields, Buttons, Date and Select Geometry | Complete | High | TP-20261014-010 | main | 2026-10-14 | [packet](completed/TP-20261014-011-shared-controls-geometry.md) |
| TP-20261014-012 | Dropdowns, Popovers and Expandable State | Complete | High | TP-20261014-010, TP-20261014-011 | main | 2026-10-14 | [packet](completed/TP-20261014-012-popovers-dropdowns-expandables.md) |
| TP-20261014-013 | Modal Overlay Focus, Stacking and Scroll | Complete | High | TP-20261014-010, TP-20261014-011 | main | 2026-10-14 | [packet](completed/TP-20261014-013-modal-viewport-focus.md) |
| TP-20261014-014 | Navbar, Responsive Tabs and Shared Spacing | Complete | High | TP-20261014-010, TP-20261014-011 | main | 2026-10-14 | [packet](completed/TP-20261014-014-navigation-shell-layout.md) |
| TP-20261014-015 | Dashboard and Direct Chart Route Detail Polish | Complete | High | TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-014 | main | 2026-10-14 | [packet](completed/TP-20261014-015-dashboard-charts-standalone-pages.md) |
| TP-20261014-016 | Transactions Data Grid, Filters and Import | Complete | High | TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-013 | main | 2026-10-14 | [packet](completed/TP-20261014-016-transactions-workbench-fields.md) |
| TP-20261014-017 | Accounts, Institutions and Account Selection UX | Complete | High | TP-20261014-010, TP-20261014-011, TP-20261014-013, TP-20261014-014, TP-20261014-008, TP-20261014-009 | main | 2026-10-14 | [packet](completed/TP-20261014-017-accounts-institutions-ux.md) |
| TP-20261014-018 | Forecast Scenarios and Assumptions UI Density | Complete | High | TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-013 | main | 2026-10-14 | [packet](completed/TP-20261014-018-forecast-assumptions-controls.md) |
| TP-20261014-019 | Planning Bill Entry, List and Allocation Controls | Complete | Normal | TP-20261014-010, TP-20261014-011, TP-20261014-014 | main | 2026-10-14 | [packet](completed/TP-20261014-019-planning-bills-allocator-ui.md) |
| TP-20261014-020 | Investments Filter, Holdings and Expandable Rows | Complete | Normal | TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-014 | main | 2026-10-14 | [packet](completed/TP-20261014-020-investments-filter-holdings-ui.md) |
| TP-20261014-021 | Settings, RSA Monitor and Auxiliary Page UX | Complete | Normal | TP-20261014-010, TP-20261014-011, TP-20261014-013, TP-20261014-014 | main | 2026-10-14 | [packet](completed/TP-20261014-021-settings-system-utility-pages.md) |
| TP-20261014-022 | Every Route Visual and Keyboard QA Gate | Complete | High | TP-20261014-010 through TP-20261014-021 | main | 2026-10-14 | [packet](completed/TP-20261014-022-full-route-visual-regression.md) |
| TP-20261014-005 | Account balance, limit and freshness contract | Complete | High | None | main | 2026-10-14 | [packet](completed/TP-20261014-005-account-balance-limit-contract.md) |
| TP-20261014-006 | APR provenance and interest inference guardrails | Complete | High | TP-20261014-005 | main | 2026-10-14 | [packet](completed/TP-20261014-006-apr-provenance-interest-estimator.md) |
| TP-20261014-007 | Optional Plaid Liabilities APR and payment metadata | Complete | Normal | TP-20261014-005, TP-20261014-006 | main | 2026-10-14 | [packet](completed/TP-20261014-007-plaid-liabilities-enrichment.md) |
| TP-20261014-008 | Accounts portfolio hierarchy and type breakouts | Complete | High | TP-20261014-005, TP-20261014-006 | main | 2026-10-14 | [packet](completed/TP-20261014-008-accounts-portfolio-type-breakout.md) |
| TP-20261014-009 | Account drill-in, truthful activity and range integrity | Complete | High | TP-20261014-008 | main | 2026-10-14 | [packet](completed/TP-20261014-009-accounts-account-detail-activity.md) |
| TP-20261014-001 | Financial Detail: Decision Hierarchy and Honest Metrics | Complete | High | None | main | 2026-10-14 | [packet](completed/TP-20261014-001-financial-detail-decision-hierarchy.md) |
| TP-20261014-002 | Upcoming Recurring: Due-First and Coverage-Aware | Complete | High | TP-20261014-001 | main | 2026-10-14 | [packet](completed/TP-20261014-002-upcoming-recurring-action-order.md) |
| TP-20261014-003 | Dashboard Date Controls: One Visible Period | Complete | High | None | main | 2026-10-14 | [packet](completed/TP-20261014-003-dashboard-shared-period-truth.md) |
| TP-20261014-004 | Dashboard Landing: Truthful Action Priority and Calm Copy | Complete | High | TP-20261014-003 | main | 2026-10-14 | [packet](completed/TP-20261014-004-dashboard-landing-truthful-actions.md) |
| TP-20261012-001 | Link Account Modal Visibility + Overlay Readability | Complete | High | None | main | 2026-10-13 | [packet](completed/TP-20261012-001-link-account-modal-visibility.md) |
| TP-20261007-002 | UI Hierarchy Foundation + App Shell | Complete | High | TP-20261007-001 | main | 2026-10-13 | [packet](completed/TP-20261007-002-ui-hierarchy-foundation-app-shell.md) |
| TP-20261007-003 | Dashboard Decision-First Recomposition | Complete | High | TP-20261007-001, TP-20261007-002 | main | 2026-10-13 | [packet](completed/TP-20261007-003-dashboard-decision-first-recomposition.md) |
| TP-20261007-004 | Transactions Action Workbench | Complete | High | TP-20261007-002 | main | 2026-10-13 | [packet](completed/TP-20261007-004-transactions-action-workbench.md) |
| TP-20261007-005 | Accounts Portfolio + Connection Hierarchy | Complete | High | TP-20261007-002 | main | 2026-10-13 | [packet](completed/TP-20261007-005-accounts-portfolio-connection-hierarchy.md) |
| TP-20261007-007 | Planning Workflow Reauthor | Complete | High | TP-20261007-002 | main | 2026-10-13 | [packet](completed/TP-20261007-007-planning-workflow-reauthor.md) |
| TP-20261007-006 | Forecast Explainable Decision Surface | Complete | Normal | TP-20261007-002 | main | 2026-10-13 | [packet](completed/TP-20261007-006-forecast-explainable-decision-surface.md) |
| TP-20261007-008 | Investments Portfolio Hierarchy | Complete | Normal | TP-20261007-002 | main | 2026-10-13 | [packet](completed/TP-20261007-008-investments-portfolio-hierarchy.md) |
| TP-20261007-009 | Cross-App Readability + Responsive + Accessibility Closure | Complete | Normal | TP-20261007-003, 004, 005, 006, 007, 008 | main | 2026-10-13 | [packet](completed/TP-20261007-009-cross-app-readability-responsive-accessibility-closure.md) |
| TP-20261013-001 | Plaid Reconnect Item Deduplication + Link Session Lifecycle | Complete | High | None (coordinate TP-20261007-009 Settings edits) | main | 2026-10-13 | [packet](completed/TP-20261013-001-plaid-reconnect-item-dedup-session-lifecycle.md) |
| TP-20261013-002 | Forecast V2 Core: Event Ledger + Liquidity Semantics | Complete | High | None (forecast-series phase 1 of 4) | main | 2026-10-13 | [packet](completed/TP-20261013-002-forecast-v2-core-event-ledger.md) |
| TP-20261013-003 | Forecast V2 Spending Intelligence: Recurrence + Residuals | Complete | High | TP-20261013-002 | main | 2026-10-13 | [packet](completed/TP-20261013-003-forecast-v2-recurring-residual-spending.md) |
| TP-20261013-004 | Forecast V2 Probabilities + Rolling Backtesting | Complete | Normal | TP-20261013-003 | main | 2026-10-13 | [packet](completed/TP-20261013-004-forecast-v2-uncertainty-backtesting.md) |
| TP-20261013-005 | Forecast V2 API + Scenarios + Frontend Integration | Complete | Normal | TP-20261013-004 | main | 2026-10-13 | [packet](completed/TP-20261013-005-forecast-v2-api-scenarios-frontend.md) |
| TP-20261007-001 | Local Schema Head Activation + Safe-to-Spend Migration Guard | Complete | High | TP-20261002-001 | main | 2026-10-09 | [packet](completed/TP-20261007-001-local-schema-head-activation.md) |
| TP-20261002-001 | Safe-to-Spend Reliability + Correct Cashflow Semantics | Complete | High | None | main | 2026-10-07 | [packet](completed/TP-20261002-001-safe-to-spend-reliability.md) |
| TP-20261001-001 | Plaid Item Connection Health + Reconnect UI | Complete | Normal | None | main | 2026-10-08 | [packet](completed/TP-20261001-001-plaid-connection-health-reconnect.md) |

## Execution notes

- Start with the highest-priority Ready packet unless the user or an explicit dependency says otherwise.
- Change `Ready` to `In Progress` when implementation actually begins.
- A `Blocked` row must include a concise blocker below this table and the concrete condition for resuming.
- `Complete` packets move to `completed/`; `Superseded` and `Cancelled` packets move to `archived/`.
- Keep completed/archived rows in this tracker for history, but active work should remain visually easy to identify.

## Blockers

None. TP-20261007-009 closed with deferred items listed in its completion report.
