# TP-20261013-005: Forecast V2 API + Scenarios + Frontend Integration

**Packet ID:** TP-20261013-005  
**Status:** Ready  
**Created:** 2026-10-13  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261013-005-forecast-v2-api-scenarios-frontend.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261013-004  
**Priority:** Normal  
**Series:** Forecast V2, packet 4 of 4 (execute 002 -> 003 -> 004 -> 005)  


## Objective

Make the V2 event-driven forecast usable in the existing Forecast page: wire trusted account-scoped V2 inputs, expose a **versioned additive** compute contract with dated cash events and P10/P50/P90 (when supported), scenario comparisons, and audit/driver details. Maintain V1 compatibility until verified and keep the completed October 7 Forecast UI hierarchy. Deliver end-to-end tested liquidity forecasts with minimal manual work.

## Confirmed current implementation

- `backend/app/routes/forecast.py::compute_forecast_route` implements `POST /api/forecast/compute`, reads JSON `user_id`, date, horizon, account filters/adjustments, gathers `_load_latest_snapshots`, `_load_historical_aggregates`, `_auto_wage_adjustments` and `_auto_rent_adjustments`, then calls V1 `backend/forecast/engine.py::compute_forecast`.
- `backend/app/routes/forecast.py::get_forecast` continues serving legacy `GET /api/forecast` through `ForecastOrchestrator.build_forecast_payload`. **Do not remove**.
- `frontend/src/composables/useForecastData.ts::fetchData` posts the current request to `/api/forecast/compute`; models `ForecastComputeResponse`, `ForecastMetadata`, `ForecastTimelinePoint`, and `ForecastSeriesMap`.
- `frontend/src/components/forecast/ForecastLayout.vue` owns scope, horizon, graph/aspect selectors, manual inputs, and source disclosures; `ForecastChart.vue`, `ForecastSummaryPanel.vue`, `ForecastBreakdown.vue`, `ForecastAdjustmentsForm.vue` already exist.
- `docs/task-packets/completed/TP-20261007-006-forecast-explainable-decision-surface.md` changed layout only. Retain its outcome-first, chart-first, details-on-demand architecture.
- Previous V2 packets provide `backend/forecast/v2_core.py`, `backend/forecast/v2_sources.py`, `backend/forecast/v2_uncertainty.py`, `backend/forecast/v2_validation.py` and typed serializers.

## Locked API / migration strategy

Version the **existing endpoint** rather than replacing it:
```http
POST /api/forecast/compute
Content-Type: application/json
```
V2 payload extends current fields, e.g.:
```json
{
 "model_version":"v2","user_id":"current-user","start_date":"2026-10-13",
 "horizon_days":90,"included_account_ids":["checking-1"],"excluded_account_ids":[],
 "adjustments":[],"scenario":null,
 "simulation":{"enabled":true,"count":500,"seed":12345,"cash_threshold":500}
}
```
Existing requests with `model_version` omitted or `v1` retain original response and behavior. V2 requires safe account ownership and scoped server-side data loading; a body `user_id` is not authorization. Use current application authentication identity mechanism when present; if not enforced in this endpoint, fail closed for cross-user account IDs and add route-level authorization tests. Do not permit user filter to bypass owner scoping, and never show data for unapproved accounts. Do **not** depend on env fallback as a substitute for access control.

V2 response retains the **existing** keys `timeline`, `summary`, `cashflows`, `adjustments`, `series`, `metadata` where coherent; adds:
```json
{
 "model_version":"v2",
 "liquidity":{"starting_cash":3000,"ending_cash":1350,"min_cash":650,"first_shortfall_date":null},
 "timeline":[{"date":"2026-10-13","forecast_balance":2950,"liquid_cash":2950,
               "p10":2800,"p50":2950,"p90":3100,"events":[...]}],
 "uncertainty":{"available":true,"risk_below_zero_any_day":0.02,
                "risk_below_threshold_any_day":0.21,"threshold":500,
                "sample_count":500,"seed":12345},
 "drivers":[{"event_id":"...","source_id":"...","date":"...","amount":-1850,
             "origin":"confirmed_recurring","confidence_label":"high"}],
 "data_quality":{"as_of_date":"2026-10-13","history_days":90,"warnings":[]},
 "scenarios":[]
}
```
Keep V1 consumers happy; if `forecast_balance` is retained in V2, explicitly define it as **liquid cash** (not net worth). Display net worth and liabilities separately. No bogus percentile fields when uncertainty unavailable; return `uncertainty.available=false` and explanatory reason.

### Ephemeral what-if scenarios

Support request-local named scenario input(s) without database migrations:
```json
{
 "scenarios":[
  {"id":"baseline","label":"Baseline","changes":{}},
  {"id":"pay-delay","label":"Paycheck 7 days late",
   "changes":{"delay_income_days":7}},
  {"id":"cut-spend","label":"Spending down 15%",
   "changes":{"residual_spending_multiplier":0.85}}
 ]
}
```
Allow `residual_spending_multiplier`, `income_multiplier`, `delay_income_days`, and additional dated signed `adjustments`; validate ranges and account/scope. Clone input assumptions **in memory** (no state mutation), call the same pure V2 engine for each; same random seed/comparable residual draws where comparisons are probabilistic so deltas reflect scenario rather than independent RNG noise. Baseline always uses identical account/date/horizon scope. Scenario result includes `ending_cash`, `min_cash`, `first_shortfall_date`, `delta_vs_baseline`, and optional probabilistic risk, not just cosmetic chart overlays.

## Required work / exact files

### Backend

- `backend/app/routes/forecast.py::compute_forecast_route`: branch on `model_version`, reject unknown versions (400), call a new orchestrating service `backend/app/services/forecast_v2_service.py` (recommended), preserve V1 path unaltered.
- V2 service: load bounded as-of per-account snapshots and historical inputs using Packet 003 source adapters, generate source calendar, calculate deterministic baseline + optional Packet 004 bands, validate scenario copies and serialize.
- `backend/forecast/models.py`: use Packet 002-004 models and emit compatible JSON structures. Do not introduce conflicting frontend-only arithmetic.
- Validate horizon <=365, scenario count <=5, simulations <=1000, bounded history and exact inclusive/exclusive dates. Return meaningful 400s for invalid input, 403/404 for unauthorized/missing data as appropriate, missing-data warnings rather than fabricated balances. If as-of cash snapshots are unavailable, say so and degrade transparently; do not silently anchor to today's balance for past start dates.
- Keep `GET /api/forecast` and `ForecastOrchestrator` behavior until an explicit later retirement packet.

### Frontend

- `frontend/src/composables/useForecastData.ts`: add typed V2 request/response mapping, loading/error/abort-or-latest-wins guard to prevent out-of-order responses replacing newer scenario/scope requests; preserve existing exports and legacy V1 fetch behavior.
- `frontend/src/components/forecast/ForecastLayout.vue`: expose concise V2 engine/scope state, fixed recurring events versus residual spend assumptions, and scenario selection/comparison. Keep baseline outcome/forecast chart first and detailed evidence under the existing disclosure. Avoid using visual design changes outside this feature.
- `frontend/src/components/forecast/ForecastChart.vue`: conditionally display baseline, P50 and shaded P10–P90 envelope when `uncertainty.available`; absent bands remain legible. Indicate liquid cash units and date axis correctly.
- `frontend/src/components/forecast/ForecastSummaryPanel.vue`: end/min cash, shortfall date or risk with appropriate observed/calculated distinction; separate investment/debt/net-worth metrics.
- `frontend/src/components/forecast/ForecastBreakdown.vue`: event sources + scheduled/residual provenance with expandable confidence/data-quality explanation. Manual overrides remain usable through `ForecastAdjustmentsForm.vue`.
- Add compact scenario comparison controls using existing Vue primitives and small view-specific component e.g. `frontend/src/components/forecast/ForecastScenarioComparison.vue`. Do not mix scenario persistence into Planning's separate data schema without a requested follow-up.
- Preserve keyboard/focus and responsive behavior per `docs/task-packets/completed/TP-20261007-006-forecast-explainable-decision-surface.md` and remaining TP-20261007-009 audit.

### Documentation

Update `docs/backend/app/routes/forecast.md`, `frontend/docs/forecast-data-contract.md`, `docs/forecast/FORECAST_ROADMAP.md` with actual V2 shapes, examples, limitations, model version default, and cutover/rollback instructions. Document data freshness, account coverage and forecast accuracy caveats as product behavior (not verbose fear language).

## Tests and implementation order

1. Backend V2 service and route validation/security tests first; retain V1 snapshot tests. Add `tests/test_forecast_v2_service.py`, `tests/test_forecast_v2_api.py`.
2. Composable V2 parsing/latest-wins and scenario input tests; add `frontend/src/composables/__tests__/useForecastData.v2.spec.ts`.
3. UI summary/chart/breakdown/scenario tests in existing `frontend/src/components/forecast/__tests__/`; add a browser E2E with mocked V2 response if viable.
4. Simulate 1/7/30/90-day horizons, two accounts plus a liability, monthly rent and biweekly paycheck, bill collision and low-cash probability; verify scenario change moves ending cash *only* by the expected modified events.
5. Preserve V1 default for backwards compatibility; place V2 behind an explicit `model_version:v2` frontend mode/feature flag until e2e acceptance tests pass. Then enable V2 for the Forecast view in the same packet if validated; leave V1 as a reversible fallback. Never silently remove V1 paths.
6. Run focused and full suites, doc checks, frontend lint/build. Mark complete only with demonstrated end-to-end results.

Commands:
```bash
pytest tests/test_forecast_v2_api.py tests/test_forecast_v2_service.py tests/test_forecast_v2_core.py tests/test_forecast_v2_sources.py tests/test_forecast_v2_uncertainty.py tests/test_forecast_v2_validation.py -q
pytest -q
cd frontend
npm run test -- --run
npm run lint
npm run build
cd ..
python scripts/check_docs.py --changed-since origin/main
```
Record any Cypress/browser blocker explicitly; do not equate unit tests with real browser verification.

## Acceptance criteria

- [ ] V1 compute and GET route response unchanged unless client explicitly requests V2.
- [ ] V2 forecasts true liquid cash with calendar events/recurrence/residuals, authenticated account scope and provenance.
- [ ] Confidence bands shown only when supported by evidence; risk semantics and source confidence labeled correctly.
- [ ] Scenario changes are replayed through the actual model, not manipulated chart outputs; deterministic comparable deltas.
- [ ] No future-as-of leakage, mixed assets/liabilities, duplicate rent/paychecks, or transfer double count.
- [ ] V2 view keeps chart/outcome priority, useful manual controls, readable mobile/keyboard experience and latest-wins fetch.
- [ ] Tests, regression/rollback plan and API documentation landed; no unsupported forecast accuracy assertions.

## Non-goals

Persistent scenario database tables, unrelated Planning/Budget UX, ARIMA replacement, investment market return prediction, debt amortization, new public API family, or deleting V1 code.

## Handoff / final workstream

Fourth and final Forecast V2 packet. Report `Workstream: TP-20261013-005`, status, commit URL, feature flag/default status, tested scenarios, rollout/rollback, exact validation and residual follow-up ideas separately.

## Execution rules (AGENTS.md)

Implement from this canonical packet, not old docs. Check the packet tracker and only the listed symbols against latest `main`; mark packet and tracker `In Progress` when starting. On completion, run tests, set `Complete`, move the packet to `completed/`, and update INDEX/TRACKER in the same commit. Keep local/origin `main` synchronized without force-push and report exact tests, deviations, blockers, and commit URL. Do not fabricate the authoring chat URL.

