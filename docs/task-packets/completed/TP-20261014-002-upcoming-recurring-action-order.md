# TP-20261014-002: Upcoming Recurring Due-First and Coverage-Aware

**Packet ID:** TP-20261014-002  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-002-upcoming-recurring-action-order.md  
**Workstream size:** One recurring timeline/UI data-load packet  
**Depends on:** TP-20261014-001 (same FinancialSummary.vue)  
**Priority:** High  
**Source reviewed:** main @ 4ef24fd358e4d630108420e4bacc98ec5733d278  
**Series:** 2 of 4

## Objective
Make "Upcoming Transactions" answer "what is due soon?" without letting pattern-confidence rankings hide earlier dates or obscure incomplete account coverage.

## Confirmed current seams
- frontend/src/components/statistics/FinancialSummary.vue: normalizeReminder(), compareReminders(), loadUpcomingRecurringTransactions(), isExtendedView watch; .sort(compareReminders).slice(0,6) sorts confidence then count BEFORE due date. First failed account Promise.all rejects the entire list. remindersFetched caches for the component lifetime; no selected accounts looks identical to "nothing due".
- frontend/src/api/recurring.js: getRecurringTransactions(accountId) -> GET /api/recurring/:accountId/recurring.
- backend/app/routes/recurring.py:get_structured_recurring: already returns due within next 7 days, fields source auto/user, account_id, amount (display string), next_due_date, days_until_due, auto_detection. Auto dates are monthly pattern estimates; user dates are manually entered. Do not claim an auto-detected transaction is a confirmed bill.

## Required edits (in order)
1. FinancialSummary.vue compareReminders(): sort next_due_date ascending (ISO lexical). Tie-break source === 'user' first, then confidence_score descending, then occurrences descending, finally stable description/account_id. Retain 6-row limit but show "+N more due in 7 days" below if the aggregated count exceeds six. Use actual API amount strings as-is (do not double-format).
2. Each row: prominent merchant/description and amount; secondary "Today", "Tomorrow", or "In N days · [short date]" plus "Scheduled" for source=user or "Likely recurring" for source=auto. Put "based on N matches" only on auto items, not confidence jargon. Header "Due in the next 7 days" with explicit "As of today", even if Financial Snapshot's historical date is set.
3. loadUpcomingRecurringTransactions(): retain getAccountSnapshot().data.selected_account_ids scope; use Promise.allSettled per account so good accounts still surface with a small partial-coverage warning. Separate states: no snapshot accounts selected, no reminders, request failed (with Retry), and partial failure. Keep per-account source IDs and deterministic rendering keys. Re-fetch when details reopen (or with <=5min TTL) so due items do not remain stale; guard late responses with request token/unmount flag. Avoid polling.
4. Preserve screen-reader-friendly status, stable row width, numeric/date scannability. Provide one low-emphasis "View transactions" link to existing /transactions; do not invent per-reminder "Pay", "Mark paid", or a /recurring route.

## Tests / validation
- frontend/src/components/statistics/__tests__/FinancialSummary.spec.js: due-before-confidence; same-day user precedence; user vs auto copy; 7+ count; selected-none; empty; all failed; partial failed; retry; stale re-open behavior; historical detailDate does NOT change next-seven-day due logic.
- If backend behavior is touched, use tests/test_routes_recurring.py; otherwise no backend changes.
- cd frontend && npm run test -- --run src/components/statistics/__tests__/FinancialSummary.spec.js && npm run lint && npm run build

## Non-goals
No new bill-paying workflow, forecasting/projection rewrite, schema migration, or recurring detection algorithm change. Do not rediscover backend endpoints beyond the named GET route.

## Acceptance / completion report
- [ ] Earliest due rows first, no implied obligation from auto-detected recurrence.
- [ ] Partial account failure does not erase successful reminders.
- [ ] Empty/partial/error states are truthful; historical snapshot context is separated from today.
Report files, tests, screenshots/inspection (if available), deviations.

## Completion report

- Reminders sort by `next_due_date`, then user before auto, confidence, occurrences, description/account. First six shown with "+N more due in 7 days".
- Rows show Today/Tomorrow/"In N days · date", Scheduled vs Likely recurring, "based on N matches" for auto only. Header "Due in the next 7 days" with "As of today".
- Per-account `Promise.allSettled`, partial-coverage warning, separate no-accounts / empty / all-failed (Retry) states, request-token guard, 5 minute TTL refresh on reopen, low-emphasis "View transactions" link.
- Backend untouched. Validation as in TP-20261014-001. Deviations: none.
