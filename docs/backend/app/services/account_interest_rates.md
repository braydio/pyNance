# `account_interest_rates`

Observed interest charges and guarded effective-rate estimation for credit-card accounts (TP-20261014-006).

## Provenance

`Account.apr` is in percentage units (`23.49`). `Account.apr_source` is one of `provider`, `manual`, `estimated`, `legacy_unverified` (migration `b2d6e8f0c4a3` marks pre-existing values `legacy_unverified`). Only `provider` and `manual` may be presented as the card's APR (`is_contractual_apr`). `apply_apr` enforces precedence: provider > manual > estimated > legacy/unknown, so an estimate never overwrites reported data.

## Observed interest

`is_qualifying_interest_charge` accepts posted, positive transactions that are clearly interest: PFC detailed `BANK_FEES_INTEREST_CHARGE`, the legacy `Bank Fees > Interest Charge` path, or an exact normalized description (`interest charge`, `purchase interest charge`, ...). Pending rows, credits/reversals, generic fees and loose "interest" substrings are excluded; re-delivered duplicates count once. `interest_paid_between` gives exact-period totals; `recent_interest_by_account` returns the trailing 90-day total for credit cards in one query.

## Estimating an effective rate

`estimate_effective_rate(cycles)` needs >= 2 contiguous complete `StatementCycle`s with a verified interest-bearing ADB (`balance_source` = `statement` or `observed_daily`), no mixed-APR/promo cycle, and per-cycle rates within 25% dispersion. Result: `100 * interest / ADB * 365 / days`, weighted by `ADB * days`, labelled `effective_annualized_charge_rate`. Otherwise `estimated_rate` is `null` with a `reason`. Reconstructed balance history never qualifies. `load_verified_cycles` currently returns no cycles (no verified ADB source yet), so the API's `estimated_rate` is `null`.

## API

`GET /api/accounts/get_accounts` adds `apr_source`, `apr_as_of`, `apr_details`, `estimated_rate`, `interest_paid_recent` (`total`, `charge_count`, `window_days`, `since`, `through`, `source`).
