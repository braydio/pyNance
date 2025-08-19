I’ve reviewed the **backend app structure**. Key findings:

- `backend/app/models.py` → large SQLAlchemy model file (≈12 KB). This is where we’d add `PlanningScenario` and `PlannedBill`.
- `backend/app/routes/` → holds modular API blueprints (accounts, transactions, teller, plaid). We should add `planning.py` here.
- `backend/app/services/` → good location if we need service-layer logic (allocation algorithms, persistence utilities).
- `backend/app/extensions.py` → initializes `db` and `migrate`, so migrations for new models will work seamlessly.

No blockers: the repo is already structured in a way that cleanly supports adding a new feature module.

---

# 📍 Roadmap: Backend + Frontend Planning Module Integration

This roadmap explicitly instructs how to implement `AGENT-IMPLEMENT-UPDATED.md` with backend support.

---

## **Phase 1 — Models**

1. Open `backend/app/models.py`.
2. Add two SQLAlchemy models:

   ```python
   class PlanningScenario(db.Model):
       __tablename__ = "planning_scenarios"
       id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
       name = db.Column(db.String(120), nullable=False)
       created_at = db.Column(db.DateTime, default=datetime.utcnow)

       bills = db.relationship("PlannedBill", backref="scenario", cascade="all, delete-orphan")


   class PlannedBill(db.Model):
       __tablename__ = "planned_bills"
       id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       scenario_id = db.Column(UUID(as_uuid=True), db.ForeignKey("planning_scenarios.id"), nullable=False)
       name = db.Column(db.String(120), nullable=False)
       amount_cents = db.Column(db.Integer, nullable=False)
       type = db.Column(db.String(20))  # "fixed" or "percent"
       value = db.Column(db.Float)      # percent allocation if type=percent
       predicted = db.Column(db.Boolean, default=True)
   ```

3. Run migration:

   ```bash
   flask db migrate -m "add planning scenario + planned bill"
   flask db upgrade
   ```

---

## **Phase 2 — Routes**

1. Create `backend/app/routes/planning.py`:

   ```python

   ```

# backend/app/models.py

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import CheckConstraint, Enum, Index, UniqueConstraint
from app.extensions import db

AllocationType = db.Enum("fixed", "percent", name="allocation_type")

class PlanningScenario(db.Model):
**tablename** = "planning_scenarios"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bills = db.relationship(
        "PlannedBill",
        backref="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    allocations = db.relationship(
        "ScenarioAllocation",
        backref="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_planning_scenarios_user_name"),
    )

class PlannedBill(db.Model):
**tablename** = "planned_bills"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = db.Column(UUID(as_uuid=True), db.ForeignKey("planning_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(120), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)  # integer cents
    due_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(80), nullable=True)
    predicted = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_planned_bills_amount_nonneg"),
        Index("ix_planned_bills_scenario_due", "scenario_id", "due_date"),
    )

class ScenarioAllocation(db.Model):
**tablename** = "scenario_allocations"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = db.Column(UUID(as_uuid=True), db.ForeignKey("planning_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)

    # "bill:<uuid>" | "savings:<name>" | "goal:<name>"
    target = db.Column(db.String(160), nullable=False)
    kind = db.Column(AllocationType, nullable=False)
    # cents if fixed; percent 0–100 if percent
    value = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("(kind = 'fixed' AND value >= 0) OR (kind = 'percent' AND value BETWEEN 0 AND 100)",
                        name="ck_alloc_value_semantics"),
        Index("ix_allocations_scenario_kind", "scenario_id", "kind"),
    )

````
2. Register in `backend/app/__init__.py` alongside other blueprints.

---

## **Phase 3 — Service Layer (Optional but Recommended)**


# backend/app/services/planning_service.py
from __future__ import annotations
from sqlalchemy.orm import joinedload
from app.models import db, PlanningScenario, ScenarioAllocation

def get_scenario_for_user(scenario_id, user_id) -> PlanningScenario | None:
 return (
     db.session.query(PlanningScenario)
     .options(joinedload(PlanningScenario.bills), joinedload(PlanningScenario.allocations))
     .filter(PlanningScenario.id == scenario_id, PlanningScenario.user_id == user_id)
     .first()
 )

def validate_percent_cap(scenario: PlanningScenario) -> None:
 pct = sum(a.value for a in scenario.allocations if a.kind == "percent")
 if pct > 100:
     raise ValueError("Percent allocations exceed 100% total")

def upsert_allocation(scenario: PlanningScenario, alloc: ScenarioAllocation) -> None:
 # Replace or add; enforce semantics and percent cap after write intent.
 db.session.add(alloc)
 db.session.flush()
 validate_percent_cap(scenario)

def delete_allocation(scenario: PlanningScenario, alloc_id) -> None:
 ScenarioAllocation.query.filter_by(id=alloc_id, scenario_id=scenario.id).delete()
 db.session.flush()
 validate_percent_cap(scenario)
---

## **Phase 4 — Frontend Service Integration**

1. Update `frontend/src/services/planningService.ts`:

* Keep `localStorage` adapter for offline/prototype mode.
* Add `api` adapter with `fetch`/`axios` calls to `/api/planning`.
* Export a toggle so devs can switch between local and API persistence.

```ts
export const planningService = {
  useLocal: true,
  async getScenarios() {
    if (this.useLocal) return getFromLocal();
    return api.get("/api/planning");
  },
  ...
}
````

2. Update reducer to support `LOAD_FROM_API` action when persistence mode is API.

---

## **Phase 5 — Tests**

- **Backend:**

  - Add `tests/test_api_planning.py`.
  - Use fixtures to simulate a user, create scenario + bills, validate CRUD + allocation.

- **Frontend:**

  - Expand `Planning.test.tsx` to cover:

    - Adding/removing bills.
    - Allocation correctness (rounding).
    - Switching persistence mode (local vs API).

---

## **Phase 6 — Docs**

- Replace `AGENT-IMPLEMENT-UPDATED.md` with `docs/PLANNING-MODULE.md`.
- Document API endpoints (`/api/planning`).
- Document frontend usage (`PlanningContext`, `planningService`).
- Add migration notes in `docs/development/`.

---

## **Phase 7 — Deployment**

- Deploy migrations + API to staging.
- Switch frontend service to API mode.
- Verify end-to-end (create scenario → persist in DB → reload in UI).

---

# 📌 Concerns Identified in Repo

- `models.py` is large (12KB). Adding new models here may bloat further. If possible, consider splitting `models/planning.py` for clarity.
- Auth: all routes must bind scenarios to a user. Repo likely has `current_user` or JWT decoding already (check `routes/accounts.py`). Planning endpoints must respect user scope.
- Tests: ensure API coverage before rollout — current test suite is comprehensive, so gaps will stand out.

---
