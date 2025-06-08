# Recurring Transactions Forecasting

## Purpose
To identify recurring financial patterns in user transactions and forecast future entries automatically.

### Components

### 1. Detection
- **File**: `recurring_detection.py`
- **Summary**: Clusters transactions by description and interval to find periodic patterns.
- **Thresholds**: Configurable minimum match count and regularity tolerance.

### 2. Bridge
- **File**: `recurring_bridge.py`
- **Responsibility**: Transforms detected patterns into forecast-compatible formats.
- **Output**: Synthetic forecast transaction entries.

### 3. Integration
- **Orchestrator**: `forecast_orchestrator.py`
- **Execution Flow*ª:
   1. Pull recent transactions.
   2. Run recurrence detection.
   3. Forecast future events via bridge module.

### 4. Data
- **Training**: `TransactionsData.csv`
- **Testing**: `TransactionMock.csv`

## Future Work
- [ ] Add user confirmation pipeline.
- [ ] Create unit tests in `tests/forecast/`.
- [ ] API documentation and UI display strategy.
- [ ] Monitoring and alerting for prediction failure cases.

## Changelog
- 2025-05-15: Initial detection module added.
- 2025-05-22: Bridge logic introduced.
- 2025-06-04: Orchestrator integration tested.
