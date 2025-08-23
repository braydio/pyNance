# pyNance Codebase Report and Feature Analysis [CODEX_REPORT]

This document provides a comprehensive tour of the pyNance codebase, followed by a feature-by-feature breakdown of areas that are partially built out or in need of completion. Each feature includes a modular, logically ordered checklist with pointers to existing documentation and code.

You can pick and choose subsections as needed; each section stands on its own.

---

## 1 Codebase at a Glance

### 1.1 What is pyNance?

    # pyNance Dashboard

    **pyNance** is a personal finance dashboard integrating Plaid and Teller APIs to

visualize and manage your financial data. It uses Flask for the backend and Vue.js for the
frontend.

README.md (/home/braydenchaffee/Projects/pyNance/README.md)

### 1.2 Key End-User Features

    ## Features

    - Link bank accounts via Plaid or Teller
    - Sync transactions and balances
    - Auto-categorize transactions using Plaid’s category tree
    - View net assets, account trends, and more
    - Built-in transaction editor with category overrides
    - Logs and debug tools for development

README.md (/home/braydenchaffee/Projects/pyNance/README.md)

### 1.3 Roadmap (Partially Done/Still To Do)

    ## Roadmap

    - Add recurring transaction detection
    - Sync investments and liabilities
    - CSV import for transaction information

README.md (/home/braydenchaffee/Projects/pyNance/README.md)

---

## 2 Project Structure

    backend/app/
    ├── config/          # Env, logging, paths, Plaid/Teller setup
    ├── routes/          # Flask blueprints (API endpoints)
    ├── helpers/         # SDK wrappers (plaid_helpers, teller_helpers)
    ├── sql/             # Business logic (account_logic, recurring_logic,

forecast_logic,…)
├── models.py # SQLAlchemy models
├── extensions.py # DB and Flask extensions
└── **init**.py # App factory & blueprint registration

    frontend/src/
    ├── components/      # Vue components (charts, tables, recurring, forecast,…)
    ├── api/             # Thin client wrappers (e.g. recurring.js)
    ├── views/           # Page‐level Vue views (Transactions.vue, Forecast.vue,…)
    ├── composables/     # Vue composables (useForecastEngine, useTransactions,…)
    ├── router/          # Vue Router config
    ├── services/        # Frontend services
    └── App.vue          # Entry point

README.md (/home/braydenchaffee/Projects/pyNance/README.md)

There are also top-level docs, design notes, and map files under docs/ (e.g.
docs/maps/backend_map.txt, docs/maps/frontend_map.txt), as well as ad-hoc changelog and
routing-refactor logs in the repo root.

---

## 3 Partially Built-Out Features & Path to Completion

Below are the major areas in flight—where there’s scaffolded code or checklist docs but
work remains—and for each a modular checklist to finish the feature end-to-end.

---

### 3.1 Recurring Transaction Detection & Management

What’s there:
• A recurring_logic.py in the backend that identifies recurring transactions.
• A full lifecycle of routes (GET, PUT, DELETE) under app/routes/recurring.py.
• Frontend components (RecurringTransactionSection.vue, RecurringCalendar.vue, etc.).
• A “feature audit” doc summarizing what’s done and what’s next.

    ## Key Observations

    - Backend model and routes **support full lifecycle**: create, update, fetch, delete

recurring transactions. - Frontend has **functional base components** for recurring management. - Merging of auto + user reminders works in `/recurring` GET route. - Recurring rule creation leverages `/recurringTx` PUT and will soon include
`/rules/new` POST. - **No current support** for _recurring rule templates_, _bulk patterns_, or _frequency
intelligence_.

frontend/src/components/recurring/00_Recurring_FeatureAudit.md (/home/braydenchaffee/Projec
ts/pyNance/frontend/src/components/recurring/00_Recurring_FeatureAudit.md)

    ### ✅ Core Functionality

    - [x] Save recurring rule via `tx_id` or `account_id`
    - [x] Edit existing rules
    - [x] Delete user-defined rules
    - [x] Merge user + auto-detected reminders in backend
    - [x] Create rule from edited transaction with confirmation

frontend/src/components/recurring/00_Recurring_FeatureAudit.md (/home/braydenchaffee/Projec
ts/pyNance/frontend/src/components/recurring/00_Recurring_FeatureAudit.md)

    ### 🚧 Frontend Enhancements

    - [x] Inline editing of transactions table
    - [x] Inline save feedback via toast messages
    - [x] Prompt rule creation on matching edit
    - [ ] Validate recurring edits (amount, date, category)
    - [ ] Modal or toast-confirmation for "always apply this rule"
    - [ ] Highlight if a rule already exists for a given condition

frontend/src/components/recurring/00_Recurring_FeatureAudit.md (/home/braydenchaffee/Projec
ts/pyNance/frontend/src/components/recurring/00_Recurring_FeatureAudit.md)

    ### 📬 Notifications / Feedback

    - [x] Toast notification on transaction update success
    - [x] Toast error on failure
    - [x] Toast feedback for rule creation or skip

frontend/src/components/recurring/00_Recurring_FeatureAudit.md (/home/braydenchaffee/Projec
ts/pyNance/frontend/src/components/recurring/00_Recurring_FeatureAudit.md)

    ### 🧭 Future Features

    - [ ] Simulate upcoming instances (next 3 months)
    - [ ] Detect recurrence patterns from transaction history
    - [ ] Merge similar entries into 1 rule
    - [ ] Graph of future recurring cashflow

frontend/src/components/recurring/00_Recurring_FeatureAudit.md (/home/braydenchaffee/Projec
ts/pyNance/frontend/src/components/recurring/00_Recurring_FeatureAudit.md)

Checklist to Complete Recurring-Tx Feature:

┌─────────────────────────────┬────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────┐
│ Phase │ Tasks  
 │
├─────────────────────────────┼────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────┤
│ Validation & UX polish │ ✓ Validate recurring rule edits (amount, date,
category)<br>✓ Modal/toast confirm “apply rule”<br>✓ Highlight existing rules
│
├─────────────────────────────┼────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────┤
│ Notifications & Feedback │ (already done for success/error)<br>Extend to rule-creation
confirmations │
├─────────────────────────────┼────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────┤
│ Recurring Pattern Detection │ - Design and implement auto pattern detection (use
find_recurring_items in sql/recurring_logic.py)<br>- Unit tests for detection algorithm │
├─────────────────────────────┼────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────┤
│ Future Visualization │ - Build recurring-cashflow graph (e.g. next-3-month
projection)<br>- Incorporate into Forecast summary │
└─────────────────────────────┴────────────────────────────────────────────────────────────
────────────────────────────────────────────────────────────────────────────────┘

---

### 3.2 Investments & Liabilities Sync (Plaid Investments)

What’s there:
A draft “product-first” integration plan for Investments under
RoutingRefactor/Investments_Integration-Summary_Overview.md.

    ## 🚧 Execution Plan

    ### Phase 1 – Foundation
    - [ ] Create `routes/product_investments.py`
    - [ ] Create `services/investments.py`
    - [ ] Add stub `get_investments` to `providers/plaid.py`

    ### Phase 2 – Feature Integration
    - [ ] Call Plaid’s `/investments/holdings` and `/transactions`
    - [ ] Normalize and merge result objects
    - [ ] Handle errors and timeouts
    - [ ] Return standardized payload to service layer

    ### Phase 3 – System Integration
    - [ ] Register route in `__init__.py`
    - [ ] Add usage to docs
    - [ ] Verify frontend compatibility or simulate requests
    - [ ] Write test payloads with Plaid sandbox data

RoutingRefactor/Investments_Integration-Summary_Overview.md (/home/braydenchaffee/Projects/
pyNance/RoutingRefactor/Investments_Integration-Summary_Overview.md)

    ## 📎 Requirements

    - [x] Plaid account tokens + account_id access (existing)
    - [ ] Response shape schema for investment holdings + transactions
    - [ ] Clarification if investment sync should be merged with transaction sync

RoutingRefactor/Investments_Integration-Summary_Overview.md (/home/braydenchaffee/Projects/
pyNance/RoutingRefactor/Investments_Integration-Summary_Overview.md)

    ## 📈 Tracking Criteria

    - [ ] Route defined and callable
    - [ ] Service stub invoked and routing properly
    - [ ] Provider logic responds with valid structure
    - [ ] Docs updated, code tested

RoutingRefactor/Investments_Integration-Summary_Overview.md (/home/braydenchaffee/Projects/
pyNance/RoutingRefactor/Investments_Integration-Summary_Overview.md)

Checklist to Complete Investments-Sync Feature:

┌───────────────────────────┬──────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────┐
│ Phase │ Tasks  
 │
├───────────────────────────┼──────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────┤
│ 1. Scaffolding │ Create routes/product_investments.py +
services/investments.py + stub in providers/plaid.py │
├───────────────────────────┼──────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────┤
│ 2. Implementation │ Integrate /investments/holdings + /investments/transactions,
normalize output, handle errors/timeouts │
├───────────────────────────┼──────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────┤
│ 3. Registration & Docs │ Register blueprint in app/**init**.py, update
docs/backend_routing_plan.md, add response‐schema definition, write sandbox tests │
├───────────────────────────┼──────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────┤
│ 4. Frontend Compatibility │ Ensure Investments view (Investments.vue) consumes the new
/investments/sync API; update UI chart rendering as needed │
└───────────────────────────┴──────────────────────────────────────────────────────────────
───────────────────────────────────────────────────────────────────┘

---

### 3.3 Transaction Import (CSV & PDF)

What’s there:
A CSV importer is implemented, but PDF parsing remains a stub.

    def import_transactions_from_pdf(filepath: str):
        """
        Placeholder for future Synchrony PDF parser
        """
        logger.warning(f"[TODO] PDF parsing not yet implemented for {filepath}")
        return {
            "status": "pending",
            "message": "PDF parsing not implemented yet",
            "file": os.path.basename(filepath),
        }

backend/app/helpers/import_helpers.py
(/home/braydenchaffee/Projects/pyNance/backend/app/helpers/import_helpers.py)

Checklist to Finish Importers:

┌────────────────────────────────────────────┬─────────────────────────────────────────────
───────────┐
│ Task │ Notes  
 │
├────────────────────────────────────────────┼─────────────────────────────────────────────
───────────┤
│ Implement import_transactions_from_pdf │ E.g. use pdfplumber or vendor-specific
parsing logic │
├────────────────────────────────────────────┼─────────────────────────────────────────────
───────────┤
│ Add tests for PDF import │ Cover one or two sample PDFs for recurring
charges │
├────────────────────────────────────────────┼─────────────────────────────────────────────
───────────┤
│ Extend CSV importer for other bank formats │ Detect bank/provider from CSV header,
automate mapping │
└────────────────────────────────────────────┴─────────────────────────────────────────────
───────────┘

---

### 3.4 Forecast Engine (Backend & Frontend)

#### 3.4.1 Backend Forecast API (Module 2)

What’s there:
A design doc for the /api/forecast route lives under
frontend/src/components/forecast/02REF_API_Integration.md. The actual endpoint
is implemented in `backend/app/routes/forecast.py` and delegates to
`ForecastOrchestrator`.

    ## 🛠️ Next Steps (Module 2)

    - [x] Implement `/api/forecast` route
    - [x] Reuse logic from `useForecastEngine.ts` (ported to Python)
    - [x] Add unit test coverage for forecast accuracy
    - [ ] Document endpoint in API spec / Swagger

frontend/src/components/forecast/02REF_API_Integration.md (/home/braydenchaffee/Projects/py
Nance/frontend/src/components/forecast/02REF_API_Integration.md)

There is also a `charts.py` module in the backend with other chart endpoints
(category_breakdown, cash_flow, net_assets, daily_net). The forecast API is served from
`backend/app/routes/forecast.py` instead.

#### 3.4.2 Full Goal-Based Checklist (Dev Checklist)

A broader, goal-based plan exists in frontend/Dev_Checklist.md. Key incomplete items:

    ## Goal 1: Ingest & Structure Data
    - [x] Set up Plaid/Teller API integration.
    - [x] Fetch and normalize transaction data.
    - [x] Store transactions in `transactions` table.
    - [ ] Fetch and store account balance snapshots in `account_history`.
    - [x] Define SQLAlchemy models in `models.py`.
    - [ ] Schedule daily sync via backend cron or task runner.

    ## Goal 2: Build and Validate Frontend Visuals
    - [ ] Build `ForecastChart.vue` using Chart.js/D3.
    - [ ] Plot forecast vs actual with mock data.
    - [ ] Add monthly/yearly toggle.
    - [ ] Embed chart in `Dashboard.vue`.
    - [ ] Validate frontend rendering logic.

    ## Goal 3: Implement Forecast Calculation Logic
    - [ ] Create forecast calculator service in `services/`.
    - [ ] Add time period logic and interest rate handling.
    - [ ] Support manual event/adjustment inputs.
    - [ ] Generate daily forecasted balances.
    - [ ] Prepare shape for chart compatibility.

    ... etc.

frontend/Dev_Checklist.md
(/home/braydenchaffee/Projects/pyNance/frontend/Dev_Checklist.md)frontend/Dev_Checklist.md
(/home/braydenchaffee/Projects/pyNance/frontend/Dev_Checklist.md)

Checklist to Complete Forecast Engine:

┌───────────────────────────────────┬──────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────┐
│ Phase │ Tasks  
 │
├───────────────────────────────────┼──────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────┤
│ Backend API │ - `/api/forecast` implemented via ForecastOrchestrator<br>- Ported useForecastEngine.ts logic to Python<br>- Unit tests in place │
├───────────────────────────────────┼──────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────┤
│ Balance Snapshot & Actuals │ - Persist daily account_history records<br>- Fallback
to transaction sums if no history<br>- Optimize queries │
├───────────────────────────────────┼──────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────┤
│ Frontend Visuals & Composables │ - Finish ForecastChart.vue and
ForecastLayout.vue<br>- Wire up live API instead of mock data<br>- Add toggle & tooltips
│
├───────────────────────────────────┼──────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────┤
│ Forecast Logic & Manual Overrides │ - Build recurrence distribution in Python & JS<br>-
Handle manualIncome & liabilityRate params<br>- Test projections │
├───────────────────────────────────┼──────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────┤
│ Documentation & Specs │ - Update API docs/Swagger<br>- Write forecast graph
spec in docs/<br>- Record performance/security considerations │
└───────────────────────────────────┴──────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────┘

---

### 3.5 Routing Refactor (Product-First Architecture)

What’s there:
A “Backend Routing Refactor Plan” doc and a suite of “Transaction Integration” proposals
under docs/backend_routing_plan.md and RoutingRefactor/TxRoutes/….

    ## 🔁 Proposed Flow

    Frontend ➝ /transactions ➝ routes/transactions.py ➝ services/transactions.py ➝

providers/plaid.py | teller.py

docs/backend_routing_plan.md
(/home/braydenchaffee/Projects/pyNance/docs/backend_routing_plan.md)

    ### Phase 1 – Bootstrapping
    - [x] Create new route file: `product_transactions.py`
    - [ ] Create `services/transactions.py`
    - [ ] Populate with Plaid + Teller call routing
    - [ ] Register route in `__init__.py`

    ### Phase 2 – Integration
    - [ ] Validate frontend can use `/transactions/sync`
    - [ ] Migrate logic from `plaid_transactions.py` and `teller_transactions.py`
    - [ ] Apply shared middleware (auth, logging, validation)

    ### Phase 3 – Cleanup
    - [ ] Deprecate old route files
    - [ ] Update `docs/backend_routing_plan.md`
    - [ ] Add test coverage

RoutingRefactor/TxRoutes/Transaction_Integration-Summary_Overview.md
(/home/braydenchaffee/Projects/pyNance/RoutingRefactor/TxRoutes/Transaction_Integration-Sum
mary_Overview.md)RoutingRefactor/TxRoutes/Transaction_Integration-Phase2.md (/home/braydenc
haffee/Projects/pyNance/RoutingRefactor/TxRoutes/Transaction_Integration-Phase2.md)

Checklist to Complete Routing Refactor:

┌────────────────────────┬─────────────────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────────┐
│ Phase │ Tasks  
 │
├────────────────────────┼─────────────────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────────┤
│ Phase 1: Bootstrapping │ ✓ routes/product_transactions.py exists<br>– Create
services/transactions.py<br>– Stub providers/plaid & teller<br>– Register in **init**.py │
├────────────────────────┼─────────────────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Integration │ – Frontend swap to /transactions/sync<br>– Migrate logic from
old routes into providers/services<br>– Add logging/auth middleware │
├────────────────────────┼─────────────────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Cleanup │ – Deprecate / archive legacy plaid_transactions.py,
teller_transactions.py<br>– Update routing docs<br>– Add tests │
└────────────────────────┴─────────────────────────────────────────────────────────────────
─────────────────────────────────────────────────────────────────────────────┘

---

### 3.6 Account Link Flow Improvements

What’s there:
A personal‐log changelog for refining the “link account” UI in
2025-05-17_pyNance_account_link_flow_refactor.md:

    # Tasklist
    - [ ] Refactor `linkPlaid` and `linkTeller` flows to be triggered on-demand
    - [ ] Move link token generation closer to button clicks instead of mount
    - [ ] No stale Plaid products – selected must exist for client instance
    - [ ] Humanized disabled controls when products are unselected
    - [ ] Patched linkConnection to controlled launching.

2025-05-17_pyNance_account_link_flow_refactor.md
(/home/braydenchaffee/Projects/pyNance/2025-05-17_pyNance_account_link_flow_refactor.md)

Checklist to Harden Link-Account UX:

┌────────────────────────────────────────┬─────────────────────────────────────────────────
────────────────┐
│ Task │ Notes  
 │
├────────────────────────────────────────┼─────────────────────────────────────────────────
────────────────┤
│ Trigger link-token generation on click │ Refactor linkPlaid/linkTeller handlers (avoid
on-mount logic) │
├────────────────────────────────────────┼─────────────────────────────────────────────────
────────────────┤
│ Enforce valid product selection │ Disable UI when no product chosen; display
human-friendly hints │
├────────────────────────────────────────┼─────────────────────────────────────────────────
────────────────┤
│ Prevent stale products in Link flow │ Ensure fetched products list is up to date
before launch │
├────────────────────────────────────────┼─────────────────────────────────────────────────
────────────────┤
│ Harden error states & toasts │ Show feedback on link failures, success,
cancellation │
└────────────────────────────────────────┴─────────────────────────────────────────────────
────────────────┘

---

## 4 Summary of Next Steps

By completing the checklists above, you will:

    * Finish **recurring-transactions** feature end-to-end (detection, UX polish, future

graph).
_ Enable **investment** syncing via Plaid `/investments` endpoints with product-first
routing.
_ Fully implement **transaction import**, including PDF parsing.
_ Deliver a **production-ready forecast engine**, with both API and UI hooked up.
_ Migrate to **product-first routing** for transactions, simplifying provider logic. \* Polish the **account-link** UX flows for Plaid and Teller.

Feel free to tackle each module in isolation. All of the above items have existing
scaffolding—either in code or in docs—so you can simply work down these checklists to
completion. Good luck!
