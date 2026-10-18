# Financial Workflows QA Gate (TP-20261016-011)

Post-feature verification of `/accounts`, `/transactions` and `/forecast` against the corrected finance
semantics. Run on 2026-10-18 against `main`. Fixture ids are scrubbed (`alice`/`bob`, `chk1`, `card`,
`hid00`..`hid16`); the world is frozen at 2026-10-16 and makes no Plaid or paid-vendor calls.

## Fixture world

`tests/test_financial_truth_gate.py::seed_world`: two checking, one savings, one credit card, one IRA, 17
hidden checking accounts, a second owner, payroll with income evidence, a card purchase, three monthly
rent-like charges, an unconfirmed own-account transfer pair, and a foreign-owner inflow.

## Backend (pytest, `.venv/bin/python -m pytest <file> -q`, per file)

| Suite | Result |
| --- | --- |
| `tests/test_financial_truth_gate.py` (new) | PASS (5) |
| `tests/test_transaction_semantics.py` | PASS (23) |
| `tests/test_recurring_detection.py` | PASS (18) |
| `tests/test_routes_recurring.py` | PASS (1) |
| `tests/test_forecast_v2_api.py` | PASS (7) |
| `tests/test_forecast_v2_validation.py` | PASS (15) |
| `tests/test_account_portfolio_metrics.py` | PASS (50) |
| `tests/test_internal_transfer_detection.py` | 4 pass, 1 FAIL (`test_detect_internal_transfer_without_description_match`) |

The failing test predates this work: it also fails on older commits. The detector now requires transfer
evidence on both sides (`classify_transfer_pair`), and the test's "Incoming" description has none. It is
a stale expectation, left untouched and tracked here.

### Acceptance checks proven by the gate test

- Plaid `+50` on checking is a `-50` cash effect and `-2000` payroll is `+2000`.
- A card purchase is one expense (`-50`); hidden accounts are excluded; the day's income plus expenses is `1950`.
- An unconfirmed savings inflow is `unclassified`, never income.
- Two recurrence scans create one `proposed` stream (never auto-confirmed); an ignored stream stays ignored; no transactions are created.
- `/scan-internal` returns only the owner's pair, mutates nothing, fails closed with 503 without an owner, and another owner cannot scan `chk1` (404).

Already covered by earlier packets and re-run above: scheduled-debt reconciliation and missing liability
coverage (`test_forecast_v2_*`), and the investment-flag conflict and hidden-account labels
(`test_account_portfolio_metrics.py`).

## Frontend

| Check | Result |
| --- | --- |
| `npm run test -- --run` | 560 pass, 36 fail (see below) |
| `npm run build` | PASS |
| `npm run lint` | 2 errors, both unused variables in files this packet did not touch |

Failing specs: `Dashboard.spec.ts` (30) and `DashboardSections.spec.ts` (1) are the known `main` failures;
`ChartRoutePage.spec.js` (4) fails because the component reads `route.query` with no router installed in
the test. `ForecastChart.spec.ts` was a stale expectation (the first toggle is now `1M`) and is fixed.

## Cypress (`cypress/e2e/financial-workflows-gate.cy.js`, new)

Matrix: 3 routes x 390/768/1280 x Nightfox/Everforest x data/empty/error with mocked APIs, asserting no
document horizontal scroll and the applied `data-theme`, plus a keyboard-focus check per route.

| Route | Result |
| --- | --- |
| `/accounts` | BLOCKED (unverified) |
| `/transactions` | BLOCKED (unverified) |
| `/forecast` | BLOCKED (unverified) |

BLOCKED: the Cypress binary is not installed on this machine (`~/.cache/Cypress` is missing) and no
preview server runs on port 4173. The spec is lint-clean but has never run, so nothing is claimed.
No screenshots were captured; no screenshot paths exist. The per-journey checks the packet lists beyond
the matrix (activity-insight counts, Recurring confirm to forecast driver, Transfer Review confirm,
100 residual events, drawer focus and contrast) are likewise unverified.

To run: `cd frontend && npx cypress install && npm run build && npx vite preview --port 4173`, then
`npx cypress run --spec cypress/e2e/financial-workflows-gate.cy.js`.
