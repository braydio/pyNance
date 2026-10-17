# TP-20261017-003: Classify Economic Flows Before Daily Net Aggregation

**Packet ID:** TP-20261017-003  
**Status:** Ready  
**Created:** 2026-10-17  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261017-003-economic-flow-classification-dashboard.md`  
**Priority:** P0  
**Workstream size:** One backend reporting-classification packet  
**Depends on:** TP-20261016-001, TP-20261016-003  
**Series:** Two packets: TP-20261017-003 then -004; existing 20261016-003 owns secure pair confirmation, -009 owns Transactions insights. Assume prerequisites land.

## Objective
Stop labeling every positive transaction delta "Income" or every negative delta "Expense". Create one read-only, owner-scoped economic-flow classification for Daily Net, summaries and transaction-list metadata, without rewriting raw bank transactions. Distinguish **economic income/expense** from **account movement**, refunds, liability settlement and unknown credits.

## Verified seams on main db9731b556c9823d407d147beb8238df169c5acd
- `backend/app/routes/charts.py::get_daily_net`: loads visible and `is_internal != True` rows, calculates `amount=display_transaction_amount(tx)`, then `amount>0 => income`, `amount<0 => expenses`. No `user_id`/account-owner bound in this query.
- `backend/app/routes/summary.py::fetch_transaction_data`: raw `Transaction.amount>0 => income` (wrong Plaid sign), `<0 => expenses`; excludes only explicit `is_internal`.
- `backend/app/sql/account_logic.py::get_paginated_transactions`: excludes `is_internal` entirely, serializes display `amount`, `transfer_type`, `internal_transfer_flag`, `category_display`, but no economic-flow type. `backend/app/routes/transactions.py::get_transactions_paginated` does not provide trusted owner to `get_paginated_transactions`.
- Oct 13 dashboard screenshot: +$200 Zelle "Transfer In - Account Transfer" and +$100 Morgan Stanley "MSPBNA BANK TRANSFER" sum exactly to displayed $300 Income; matching posted debit counterpart is not shown. The $200 self-transfer is user-confirmed; $100 transfer is a **candidate**, not independently proven. Do not encode either personally identifying memo as permanent business logic.

## Do not rediscover / exact edits
1. `backend/app/services/transaction_flow_classification.py` **(new)**: pure `classify_reporting_flow(tx, account, *, linked_pair=None, user_decision=None) -> {flow_kind, confidence, reason_codes, signed_account_delta, economic_amount}`. Use canonical `transaction_semantics.canonical_account_delta` from 001, exactly once. Kinds `income|expense|transfer|debt_settlement|refund|investment_movement|unclassified`; monetary math Decimal cents. `economic_amount` only for verified income/expense; refunds offset attributable expense and never become wages. Separate `signed_account_delta` for bank balance movement. Always preserve original bank signed amount.
2. Classification precedence: trusted user correction > confirmed same-owner `is_internal` / verified `internal_match_id` > strong own-account transfer evidence (Plaid category `transfers_in_account_transfer`, distinct owned-account counterpart, verified self-name+account context) > confirmed income or economic expense category/provider > unclassified. Explicit income evidence (payroll, interest/dividends) remains income; Zelle/ACH alone is NOT proof of own transfer. One-sided own-account inflows may be `transfer` with reason `unpaired_own_account` when provenance strong; ambiguous brokerage-related deposits use `unclassified` and `needs_review` instead of invented income. Do NOT auto-set `Transaction.is_internal=True` or fabricate matched pairs for unpaired evidence. Respect user classifications, and do not infer solely from merchant string or positive sign.
3. `backend/app/routes/charts.py::get_daily_net`: owner-bound query using trusted principal (follow 003; fail closed if owner unavailable rather than aggregate other users), exclude pending/hidden; classify each posted transaction once; rollup by `flow_kind`. Keep backward-compatible `income/expenses/net/transaction_count` shape, but `net=income+expenses` (economic net); add `transfer_in/transfer_out/debt_settlement/refunds/unclassified_inflows/coverage` fields, with explicitly documented separate cash balance movement. A credit-card interest expense can count economically, but a credit-card principal payment isn't a second spending event.
4. `backend/app/routes/summary.py::fetch_transaction_data`: use the **same** classification/normalization contract (no raw sign CASE). Keep stats shape; match Daily Net and owner scope. Audit routes used for account net_changes/other Net Income consumers only if same behavior; do not expand to unrelated forecasting code.
5. `backend/app/sql/account_logic.py::get_paginated_transactions`: add `reporting_flow_kind,flow_confidence,flow_reason_codes` to serializer for every visible entry and a parameter to retain confirmed transfer entries in **daily modal** history via `include_transfers=true`; default existing Transactions explorer behavior may stay unchanged. `backend/app/routes/transactions.py::get_transactions_paginated`: support that parameter with ownership check using server principal, never caller-supplied user id. Avoid N+1 pair lookup; batch/join if needed. Reuse exact classifier, no JS copy.
6. Do not assume every `financial_other_debt_payments` event is external spending or internal own-account movement. Principal/interest decomposition only when sourced; disclose unknown; preserve economic spending vs cash-payment difference.

## Acceptance tests and fixtures (synthetic, not user's banking data)
- Checking +$200 verified own Zelle transfer => `transfer`, **0 income**; matching other account -$200 => 0 economic spend, both visible in transfer history.
- Checking +$100 with unpaired brokerage-bank-transfer descriptor and uncertain ownership => `unclassified`/review, **0 confirmed income**; when ownership evidence arrives => `transfer`. No unwarranted automatic pair/decision.
- Posted payroll +$1000 => income $1000; refund +$25 => refund not income; credit-card interest -$15 => expense; loan principal payment => `debt_settlement`, not wage income or duplicated consumption; unclassified deposit not silently income.
- Main screenshot's +$200 and +$100 must not produce $300 recognized income. Cross-owner/hidden/pending omitted; repeated runs deterministic; bank movements unchanged.
- Chart and summary economics equal for same owner/date, match posted transaction-list classifications. No hidden owner leakage or paid API calls.

## Commands / boundaries
`pytest tests/test_transaction_flow_classification.py tests/test_charts_daily_net.py tests/test_transfer_analytics_exclusion.py tests/test_transaction_insights.py -q` (create missing focused files as necessary); `pytest tests/test_internal_transfer_detection.py tests/test_forecast_v2_adapters.py -q`.
No schema migration, no bulk auto-modification, no transaction deletes, no new Plaid calls, no UI design changes. Build only named classifier and consumers; no broad repo search.
Implementation: read AGENTS + packet README/INDEX/TRACKER; mark In Progress; validate exact symbols; implement/test; move completed and update INDEX/TRACKER in same commit; push main without force; report tested owner/date reconciliations and any unavailable runtime tests. Next TP-20261017-004.
