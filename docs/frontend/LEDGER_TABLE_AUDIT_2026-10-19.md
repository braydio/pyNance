# Ledger and Table Audit (2026-10-19)

Result of TP-20261019-002 to 005. Every table and table-like list, its data source, what its totals mean, and how missing data behaves. Shared anatomy: `docs/frontend/THEMING_GUIDE.md` (ledger tables, surface roles). Summary contract: `docs/frontend/TRANSACTIONS_TABLE_SUMMARIES.md`.

## Canonical tables (`components/tables/`)

| Component | Data source | Row scope | Totals scope | Missing/stale | Filter owner | Visual status | Tests |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UpdateTransactionsTable` | `/api/transactions/paginated` via `useTransactions` | One server page | All matching (server `/summary`, shown by `Transactions.vue`) plus page subtotal | Totals unavailable + Retry, stale label; never $0 | Server (single filter set) | Ledger shell, caption, Reset filters | `UpdateTransactionsTable.spec.js`, `Transactions.spec.js` |
| `AccountsTable` | `/api/accounts/get_accounts` | Filtered accounts | Assets and liabilities separate (`portfolioTotals`), group subtotals | "Unavailable" for unknown balance; hidden called out | Component (search, type, hidden) | Ledger bar | `AccountsTable.spec.js` |
| `InstitutionTable` | `api.getInstitutions` | Institutions, expandable accounts | Per-institution line: assets, owed, unavailable, hidden | "Unavailable" balance | None | Single scroll owner | `InstitutionTable.spec.js` |
| `MasterTxidTable` | Parent-supplied list | Loaded page | None (legacy; no new KPI without data) | n/a | Component | Button sort headers, `aria-sort`, caption | none new |
| `ModalTransactionsDisplay` | Parent-supplied day/merchant rows | Rows passed in | None (local rows are not a full set) | "No transactions found." | Parent | Caption, keyboard rows | `ModalTransactionsDisplay.spec.js` |
| `TransactionsTable` | Parent-supplied rows (legacy dashboard consumer) | Rows passed in | None (legacy checked) | n/a | Parent | Caption, column scopes | `TransactionsTable.cy.js` |

## Table-like lists

| Component | Data source | Totals scope | Notes | Tests |
| --- | --- | --- | --- | --- |
| `Investments.vue` holdings | `fetchHoldings` | Filtered holdings value vs entire connected value, counts; institution subtotal when more than one | Account rows reconcile to child holdings | `Investments.spec.js` |
| `Investments.vue` transactions | `fetchInvestmentTransactions` (paged) | **Page only**, grouped by provider type (buys, sells, dividends, transfers, cash, fees); never a profit figure | `role=table` grid with column headers | `Investments.spec.js` |
| `AccountPortfolioList` | Accounts prop + `accountPortfolio.js` | Assets and liabilities separate for shown accounts; fixed all-accounts comparator; per-group subtotal | Unknown balances and hidden accounts stated | `AccountPortfolio.spec.js` |
| `RecurringTransactionSection` | `/api/recurring` | Confirmed plans due in next 30 days, one due date each, split in/out, estimated count | Suggestions and ignored/ended excluded and counted | `RecurringTransactionSection.spec.js` |
| `BillList` / `PlanningSummary` | Scenario bills | Next 30 days (entered vs predicted separate); all listed amounts labelled "mixed cadence, not a monthly total" | One scenario's bills only | `BillList.spec.ts` |
| `InternalTransferScanner` | `/api/transactions` scan | Pair count; "loaded pairs only" when truncated | No totals, no extra API | `InternalTransferScanner.spec.js` |
| `TransactionReviewModal` | Parent-supplied page | Position "n of total" already shown | Coverage unchanged | `TransactionReviewModal.spec.js` |
| `ForecastSummaryPanel` | Forecast payload | Cash projection kept apart from debt and net-worth lines (existing) | Reviewed, no change | `ForecastSummaryPanel` specs |

## Not done

- No browser screenshots at 390, 768 or 1280px, and no Cypress runs.
- The holdings grid still uses div rows with expandable child rows; only the transaction grid has full table roles.
- No all-matching investment transaction total: the backend has no such summary.
