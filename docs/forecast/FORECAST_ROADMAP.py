Notes

The repository contains a partial forecasting implementation. The core design is described in docs/forecast/FORECAST_PURPOSE.md, which introduces forecast_engine.py, forecast_stat_model.py, and forecast_orchestrator.py.

A status summary in docs/BACKEND_STATUS.md states that only basic endpoints exist with mock logic. Integration with live data and delta calculations is still pending.

The detailed frontend checklist in frontend/src/components/forecast/03REF_Development_Planning.md shows that UI scaffolding and mock integration are complete, while live engine wiring, investment modeling, and error handling remain open tasks.

The proposed API response format for /api/forecast is outlined in frontend/src/components/forecast/02REF_API_Integration.md.

Summary

Current State
Backend

Has a placeholder ForecastSimulator and a basic route /api/forecast/forecast returning projected balances using recurring transactions. It relies on forecast_balance.py, which still contains issues (e.g., self.freq_map.set bug) and does not leverage the more advanced ForecastEngine or ForecastOrchestrator.

ForecastEngine, ForecastStatModel, and ForecastOrchestrator are present but not wired into API endpoints.

Account balances are updated via provider helpers (plaid_helpers.py, teller_helpers.py) to populate AccountHistory, forming the data source for forecasting.

Frontend

Contains a suite of forecast components: ForecastLayout.vue, ForecastChart.vue, ForecastBreakdown.vue, and a composable useForecastEngine.ts for deriving labels, forecast, and actual arrays.

A mock page (ForecastMock.vue) demonstrates the feature using static data.

useForecastData.ts is prepared to fetch /api/recurring-transactions and /api/account-history but these routes are not yet implemented.

Required Backend Dependencies
AccountHistory integration – Ensure provider sync functions call update_account_history() after fetching balances (already documented in backend/app/helpers/plaid_helpers.py and teller_helpers.py).

Recurring detection pipeline – Implement recurring_bridge.py to persist detected recurring transactions as planned in backend/app/services/FORECAST_RECURRING_ROADMAP.md.

Forecast engines – Connect ForecastEngine and ForecastOrchestrator to new API routes for summary and per-account forecasts (roadmap lines 121‑134).

Endpoint specification – Follow the /api/forecast design with query parameters user_id, view_type, manual_income, liability_rate and return labels, forecast, actuals, metadata as described in 02REF_API_Integration.md.

Response Structure
{
  "labels": ["May 1", "May 2", "May 3", ...],
  "forecast": [4200.0, 4320.0, 4350.0, ...],
  "actuals": [4200.0, 4280.0, null, ...],
  "metadata": {
    "account_count": 3,
    "recurring_count": 5,
    "data_age_days": 0
  }
}
(Example from 02REF_API_Integration.md)

Frontend Forecasting Status
Forecast chart, summary panel, breakdown panel, and adjustments form are fully scaffolded.

useForecastEngine.ts computes forecast and actual lines; ForecastLayout.vue wires these components together.

The checklist shows only mock data is currently used; live backend integration and advanced analytics are pending.

Roadmap for Completing the Forecast Feature
Recurring Detection to DB

Finalize recurring_detection.py and implement recurring_bridge.py to upsert recurring transactions into the database.

Expose new endpoint /api/recurring/... for listing and managing these rules.

Balance History Sync

Ensure every account sync (Plaid/Teller) updates AccountHistory through update_account_history() to provide historical data for actual line calculation.

Forecast Engine Integration

Fix forecast_balance.py bug (freq_map.get).

Build an orchestration layer in forecast_orchestrator.py to combine rule-based forecasts with optional statistical models.

Implement an internal service function such as build_forecast_payload(user_id, view_type, manual_income, liability_rate).

API Routes

Replace /api/forecast/forecast with routes:

GET /api/forecast – returns forecast/actual lines using orchestrator. ✅ Implemented June 2025

POST /api/forecast/calculate – accepts manual income/liability overrides. ✅ Implemented

Optionally add GET /api/forecast/events and /api/forecast/account/{account_id} as per roadmap.

Frontend Integration

Update useForecastData.ts to hit the new endpoints.

Replace mock data in ForecastLayout.vue with fetched results and wire the manual income/liability inputs to POST /api/forecast/calculate.

Testing & Validation

Add unit tests for new endpoints (check correct JSON structure and edge cases).

Create frontend E2E tests verifying the chart toggling, data rendering, and manual input flow.

Documentation & Cleanup

Update API reference and service docs with final route usage.

Mark completed tasks in 03REF_Development_Planning.md and the roadmap document.
