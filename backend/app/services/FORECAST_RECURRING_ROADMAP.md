# Forecast + Recurring Logic Integration Roadmap

This document outlines a step-by-step implementation plan to integrate robust recurring detection with forecasting logic in `pyNance`, keeping concerns cleanly separated and aligned with the project's backend architecture principles.

---

## 🔄 Objective

Integrate recurring transaction detection and forecasting into a cohesive system that:

- Detects and stores recurring patterns in the database
- Simulates future account balances based on those patterns
- Exposes useful, interactive, and consistent forecasting APIs

---

## 🌐 Context

### Current Modules

| Module      | Purpose                                   |
| ----------- | ----------------------------------------- |
| `routes/`   | API endpoints                             |
| `db_logic/`      | DB read/write logic                       |
| `services/` | Core business logic and algorithm engines |
| `models.py` | SQLAlchemy models                         |

### New Additions

- `services/recurring_detection.py`: Detects recurring patterns from transaction history
- `routes/forecast.py`, `routes/recurring.py`: Forecasting and recurring endpoints
- `db_logic/recurring_logic.py`: DB-level logic for recurring insertion

---

## ✍️ Implementation Plan

### 🔄 Phase 1: Connect Detection to Persistence

#### 📂 New File

- `services/recurring_bridge.py`

#### 🔊 Role

- Takes the output from `RecurringDetector`
- Matches against existing `RecurringTransaction` records
- Uses `db_logic/recurring_logic.py` to upsert candidates

#### 🔎 Tasks

- [ ] Normalize detection output to model fields
- [ ] Use `description`, `amount` to check for duplicates
- [ ] Insert or update DB as needed (call into `db_logic/`)
- [ ] Return response with status (inserted/updated/matched)

### 🌟 Phase 2: Forecast Engine

#### 📂 New Files

- `services/forecast/forecast_balance.py`
- `services/forecast/__init__.py`

#### 🔊 Role

- Uses `RecurringTransaction`, current balances, and APR
- Projects future balance trajectory

#### 🔎 Tasks

- [ ] Load recurring events for account (via SQL)
- [ ] Simulate cash flow over next N days
- [ ] Handle interest-bearing credit balances
- [ ] Expose stepwise forecast output (date, predicted balance)

### 📈 Phase 3: API Exposure

#### 📂 File Updated

- `routes/forecast.py`

#### 🔊 Endpoints

- `GET /forecast/{account_id}`: returns future balance
- `GET /forecast/events`: returns estimated recurring events

---

## 📊 File & Module Map

| File                                    | Role                           | Type      |
| --------------------------------------- | ------------------------------ | --------- |
| `services/recurring_detection.py`       | Pattern recognition engine     | Service   |
| `services/recurring_bridge.py`          | DB sync bridge for recurrence  | Service   |
| `db_logic/recurring_logic.py`                | Upsert recurring items         | SQL       |
| `services/forecast/forecast_balance.py` | Simulate future cash flow      | Service   |
| `routes/forecast.py`                    | Forecast endpoint handler      | API Route |
| `routes/recurring.py`                   | Recurring management interface | API Route |

---

## ⚠️ Risks and Edge Cases

- ❌ **Duplicate entries**: detecting already-logged recurring items if signature logic changes
- ❌ **Inaccurate frequency**: noisy data or irregular gaps might cause bad predictions
- ❌ **APR computation**: different cards/accounts might have complex interest schedules
- ❌ **Timezone and date drift**: especially around months with variable lengths
- ❌ **Mismatch in prediction & user expectation**: need clear explanations in frontend

---

## ✅ Development Checklist

### Phase 1: Detection to DB Sync

- [ ] Create `recurring_bridge.py` in `services/`
- [ ] Normalize and map detector output
- [ ] Validate against DB (existing recurring)
- [ ] Call into `db_logic/recurring_logic.py`

### Phase 2: Forecast Balance Engine

- [ ] Create `forecast_balance.py`
- [ ] Load recurring and current balance
- [ ] Forecast daily deltas
- [ ] Handle credit APR logic

### Phase 3: Forecast Routes

- [ ] Add `/forecast/account` route
- [ ] Add `/forecast/events` route
- [ ] Connect routes to engine logic

---

## 🎯 Goal

By separating responsibilities and aligning with the repo’s structure, this implementation will:

- Maintain clear domain boundaries
- Improve testability and reusability
- Enable reliable forecasting of future balances
- Create a foundation for proactive alerts and planning

---
