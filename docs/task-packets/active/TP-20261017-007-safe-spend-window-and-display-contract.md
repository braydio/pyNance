# TP-20261017-007: Safe-to-Spend Protection Horizon and Headline Truth

**Packet ID:** TP-20261017-007  
**Status:** Ready  
**Created:** 2026-10-17  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261017-007-safe-spend-window-and-display-contract.md`  
**Workstream size:** One API decision/horizon + existing card semantics packet  
**Priority:** P0  
**Depends on:** TP-20261017-005, TP-20261017-006  
**Series:** Upstream 005/006, then this packet, then TP-20261017-001 (recurring obligations) and -002 (bill explanation). Do not implement future recurring projection here.

## Objective
Display an allowance that is actually *safe through the protection horizon*, correctly distinguish a per-day allowance from total remaining cash, and show the exact date windows/payday uncertainty.

## Verified seam (main 06c1ae48)
- `backend/app/services/safe_to_spend.py::_horizon_end`: today = today, week = today+6, until_payday = **payday inclusive** or today+14 (15 inclusive days when unknown).
- `build_safe_to_spend_payload`: `raw=C-plannedBills-$250-spent_today`, clamps, `per_day=raw // inclusive_days`, `amount_cents` switches meaning between total (Today) and per-day (Week/Payday). A bill due tomorrow is not protected by "Today". Confidence depends on presence of a cash account and presence of any PlannedBill, not history/sync quality.
- `frontend/src/components/dashboard/SafeToSpendCard.vue`: one large `payload.amount_cents`; `amountCopy='available today'|'per day'`; "This Week" suggests calendar week but is a rolling 7 days. `frontend/src/views/Dashboard.vue::loadSafeToSpend` queries mode independently from 3M/YTD historical charts.
- `backend/app/routes/dashboard.py::get_safe_to_spend` default buffer hardcoded $250; user-specific settings not persisted.

## Do not rediscover / exact implementation
1. `backend/app/services/safe_to_spend.py`: derive **two separate inclusive windows**, `display_start/end` and `protection_start/end`. `Today` displays **today's daily discretionary allowance** but protects upcoming obligations until *the day before the next validated paycheck* (if known), else a clearly labeled rolling 14-day safety horizon; a tomorrow bill is not free money today. `Next 7 Days` displays a rolling 7-day allowance (today..today+6), protecting at least through the greater of its own horizon and the same pre-payday/14-day protection window. `Until Payday` shows through `next_payday-1`, excluding unreceived paycheck cash; if prediction unverified use `next_payday=null` and a labeled 14-day fallback (today..today+13) rather than claiming payday. If payday is **today but not posted**, don't assume money available; flag `awaiting_payday_post`, treat as fall-back safe mode until receipt. `MODE_WINDOWS` constant and `_horizon_end` must match exact inclusive-day semantics.
2. **Keep today's displayed allowance defensible.** Let `total_protected_room = max(0, accessible_cash - known_future_obligations_through_protection_end - buffer - only verified-not-yet-in-available-balance pending debits)`. Define `daily_allowance_cents = floor(total_protected_room / max(1, protection_end-as_of+1))`. Today headline is `daily_allowance_cents` (not all remaining cash); Week and Until Payday show per-day allowances based on their display windows but **never** inflate above the shared protection-aware daily allowance just by shortening the label. Return `total_horizon_cents`, `per_day_cents`, `amount_cents` compatibility keys but add `total_protected_room_cents`, `display_window`, `protection_window`, `calculation_version`; document which term each means. **No artificial increase** when switching Today to Week with identical cash/obligation evidence. If user wants *entire discretionary cash*, show separate less-prominent "Total protected spending room"; don't call it today's allowance.
3. **Bill sums:** planned occurrence expansion / recurring merge belongs exclusively to TP-20261017-001. This packet temporarily reuses existing `_upcoming_bill_payload` with its **protection end**, not display end, and labels incomplete coverage. Existing 001 must project all eligible due obligations through `protection_end` while returning `due_today_cents` separately; none counted twice; future bills not mislabeled "due today."
4. `confidence`: derive from `cash_coverage`, `payday_prediction`, and `obligation_coverage`; unsupported/estimated dates must not yield `ready` just because any `PlannedBill` exists. Separate `status` (tightness) from `confidence` (evidence completeness), and include human-readable warnings.
5. `frontend/src/components/dashboard/SafeToSpendCard.vue`, `frontend/src/components/dashboard/NetOverviewSection.vue`, `docs/frontend/safe-to-spend.md`: label button "Next 7 Days" not "This Week"; show `Daily allowance` prominently, protected total as secondary, exact `display_window` and `protection_window` dates, inferred vs confirmed payday source and confidence, "$250 default buffer" disclosed. Historical dashboard 3M/YTD ranges do NOT alter this decisioning. Do not add a massive settings redesign or duplicate TP-20261017-002's expandable obligation table.
6. `tests/test_safe_to_spend_service.py`, `tests/test_safe_to_spend_integration.py`, `frontend/src/components/dashboard/__tests__/SafeToSpendCard.spec.js` (new or extend): fixed `as_of=2026-10-17`, payday Oct 30 => protection window Oct17..Oct29, unverified => fallback Oct17..Oct30 (14 days), rolling week Oct17..23; payday money not in opening cash until actually posted; synthetic $700 due Oct21 protected **even in Today** after TP-20261017-001 lands; headline not total; no dependence on historical chart presets; no-data/warnings/overdraft scenario. For buffer and negative balances use 006.

## Non-goals / handoff
No recurring detector, bank balance mutation, new provider APIs, paid lookups, unknown paychecks inserted as cash, alternative scenarios or broad dashboard restyle. `pytest tests/test_safe_to_spend_service.py tests/test_safe_to_spend_integration.py -q`; `cd frontend && npm run test -- --run src/components/dashboard/__tests__/SafeToSpendCard.spec.js && npm run build`. Read AGENTS and packet controls, mark In Progress/Complete with tracker + canonical location, and report exact simulated horizon math and tests.
