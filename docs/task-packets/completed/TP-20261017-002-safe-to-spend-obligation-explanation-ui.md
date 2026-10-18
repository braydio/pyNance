# TP-20261017-002: Explain Recurring Reserves and Missing-Coverage Reasons in Safe-to-Spend

**Packet ID:** TP-20261017-002  
**Status:** Complete  
**Created:** 2026-10-17  
**Last updated:** 2026-10-18  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261017-002-safe-to-spend-obligation-explanation-ui.md`  
**Workstream size:** One UI/verification packet  
**Priority:** P1  
**Depends on:** TP-20261017-001, TP-20261017-007, TP-20261016-005  
**Series:** Follow-on packet 2/2; only integrate, do not reimplement scanner or safe-spend math.  

## Objective
Show exactly why a monthly bill is / is not reserved in the selected Safe-to-Spend window, with an actionable review route and coverage status; no unexplained missing ~$700 obligations.

## Do not rediscover: exact files/symbols
- `frontend/src/components/dashboard/SafeToSpendCard.vue`: `payload`, `modeOptions`, `formatCents`, `horizonLabel`, `confidenceLabel`.
- `frontend/src/components/dashboard/NetOverviewSection.vue`: existing fetch/refresh and mode wiring (only if present on main).
- `frontend/src/views/Transactions.vue` and `frontend/src/components/recurring/RecurringTransactionSection.vue`: existing review opening from 005; link/reuse, don't duplicate review UI.
- `docs/frontend/safe-to-spend.md` (document API components / horizon semantics).
- `frontend/src/components/dashboard/__tests__/SafeToSpendCard.spec.js` **(new if absent)**; `tests/test_safe_to_spend_integration.py` (contract checks).

## Confirmed current seam (main 65433b2315bd44904079a2b090ccf6502a96ddd0)
`SafeToSpendCard.vue` renders one "Upcoming bills" amount from `components.upcoming_outflows_cents`, a generic `confidence`, and a horizon label; it does not list reserved bills, sources, dates, or anything requiring review. `modeOptions` are Today / Until Payday / This Week. This can make a payment due after today's horizon appear missing even when it exists.

## Exact implementation
1. **Keep the existing simple card.** Under the existing "Upcoming bills" figure add a single expandable "What's reserved?" disclosure with grouped totals `Planned`, `Confirmed recurring`, `Provisional recurring`, with `due_date`, account display, amounts, and date-sorted source rows. Render `estimated` as "estimated", do not call provisional "confirmed". Use packet 001 `upcoming_bills` and component splits; no second client computation. Show a compact "Needs review" amount/count (not included in reserve), linking to the 005 Recurring review UI via its existing tab flow. Avoid leaking raw transaction/account IDs in visible labels.
2. **Explain horizon vs detection.** For `today`, distinguish **due today** vs **future bills protected before payday**. If a recurring debit is due Oct 21, not today, display its next date and protected reserve as a future obligation when in TP-20261017-007's protection window. For `week` the display covers `as_of..as_of+6d`, while protection may extend beyond it; until payday protects through the day *before* an inferred posted-paycheck date (fallback is explicitly labeled 14 inclusive days as in TP-20261017-007). If a known obligation is not reserved, display a precise reason from `obligation_coverage` or candidate `reason_codes`: insufficient history, missing owner/account, pending-only, ignored, outside window, candidate needs review, or stale import. Never say "no recurring bills" merely because none were imported.
3. **Ensure refresh.** Re-fetch Safe-to-Spend on horizon change and after Confirm/Ignore/Edit in existing recurring UI. Reuse existing events/store rather than periodic polling, extra API, or page reload; show loading and error. No new global state store unless existing flow makes it necessary.
4. **Accessibility/design scope.** Use existing card tokens and spacing, native `button` disclosure with `aria-expanded`, keyboard behavior, overflow-safe mobile 390px. Do not change the dashboard's overall color palette or layout. Keep core numeric amount prominent.

## Fixtures and acceptance
- Synthetic posted $700 monthly recurrence due 2026-10-21, as_of 2026-10-17: Today shows Oct 21 as future and **-$700 reserved toward the pre-payday protected total**, $0 due today; Week also shows **-$700** in provisional or confirmed split, date/amount in disclosure; stable total matches server `upcoming_outflows_cents`.
- Both `PlannedBill` and recurrence present: exactly one $700 row; user rejects candidate: reserve disappears next fetch, reason "ignored"; no history: coverage warning rather than false "none".
- 390px and 1280px; no truncated amounts; server error; zero bills; reader accessible; no client double addition.

## Test commands
`cd frontend && npm run test -- --run src/components/dashboard/__tests__/SafeToSpendCard.spec.js && npm run build`; `pytest tests/test_safe_to_spend_integration.py -q`. Verify dashboard Today/Week/Until Payday with fixed mocked API, no live Plaid request.

## Non-goals
No new detector, no backend financial algorithms, no whole-dashboard restyle, no recurring-review rewrite, no auto-payment or changes to accounts.

## Completion / agent handoff
Read `AGENTS.md`, task-packets README/INDEX/TRACKER and only these named surfaces. Mark In Progress; implement and validate; commit/push main without force; mark Complete, move to completed, update index+tracker atomically; report test outputs, screenshots if UI was exercised, and any coverage blockers.

## Completion report (2026-10-18)

- Files: `frontend/src/components/dashboard/SafeToSpendCard.vue`, `frontend/src/components/dashboard/__tests__/SafeToSpendCard.spec.ts`, `frontend/src/views/Transactions.vue` (`?tab=Recurring`), `frontend/src/views/__tests__/TransactionsRecurringHandoff.spec.js`, `docs/frontend/safe-to-spend.md`.
- Tests: `npx vitest --run` on the card, handoff, Transactions and dashboard section specs pass except `DashboardSections.spec.ts` "marks exactly one period control active" (known failing on `main`); `npm run build` succeeds; backend contract covered by `tests/test_safe_to_spend_integration.py` (13 passed).
- Refresh: the dashboard has no keep-alive and refetches on mount, so recurring decisions made in the Recurring tab apply on return; no polling or new store added (per packet).
- Not done: no screenshots at 390px/1280px were captured (no browser session); layout relies on wrapping rules (`overflow-wrap`, `nowrap` amounts).
