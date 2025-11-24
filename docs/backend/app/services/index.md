# backend/app/services Documentation

---

## Index of Service Modules

### Accounts & History

- [`account_history.py`](account_history.md): Reverse-map daily balances from transaction deltas.
- [`balance_history.py`](balance_history.md): Persist and retrieve normalized balance histories from the database.
- [`enhanced_account_history.py`](enhanced_account_history.md): Cache-aware wrapper that orchestrates history recomputation and storage.
- [`account_snapshot.py`](account_snapshot.md): Manage preferred snapshot selections for dashboard widgets.
- [`account_groups.py`](account_groups.md): CRUD and ordering logic for customizable dashboard account groups.

### Forecasting

- [`forecast_balance.py`](forecast_balance.md): Daily cashflow and forward balance projections.
- [`forecast_engine.py`](forecast_engine.md): Core system for predictive modeling and spending estimation.
- [`forecast_orchestrator.py`](forecast_orchestrator.md): High-level integration and coordination of forecasting components.
- [`forecast_stat_model.py`](forecast_stat_model.md): Statistical regressions for category forecasting.

### Recurring Transactions

- [`recurring_bridge.py`](recurring_bridge.md): Synchronization layer between new transactions and recurrence tracking.
- [`recurring_detection.py`](recurring_detection.md): Pattern mining to infer recurring flows.

### Synchronization & Storage

- [`plaid_sync.py`](plaid_sync.md): Plaid `/transactions/sync` integration and reconciliation logic.
- [`sync_service.py`](sync_service.md): Orchestrates transaction ingestion from APIs or files.
- [`transactions.py`](transactions.md): Core logic for interacting with transaction data.

### Arbitrage

- [`arbit_metrics.py`](arbit_metrics.md): Retrieves metrics from the Arbit exporter.

### Planning

- [`planning_service.py`](planning_service.md): In-memory prototype for bills and allocation planning workflows.

---

Consult the linked documents above for detailed responsibilities, function summaries, and integration notes for each service module.

## Cross-References

- Routes that rely heavily on this layer include [Transactions](../routes/transactions.md), [Plaid sync](../routes/plaid_transactions.md), and [Accounts](../routes/accounts.md). Use the linked route docs alongside the services above for end-to-end context.
