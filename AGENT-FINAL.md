---
# 📍 Roadmap: Backend + Frontend Planning Module Integration (Finalized)

This roadmap extends `AGENT-IMPLEMENT-UPDATED.md` with a **backend + frontend integration** that is repo-accurate, scalable, and consistent with your React/TS frontend.
---

## **Phase 1 — Models**

Open `backend/app/models.py`. Add **three models**:

```python
# backend/app/models.py
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from app.extensions import db

AllocationType = db.Enum("fixed", "percent", name="allocation_type")


class PlanningScenario(db.Model):
    __tablename__ = "planning_scenarios"

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
    __tablename__ = "planned_bills"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("planning_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

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
    __tablename__ = "scenario_allocations"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("planning_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "bill:<uuid>" | "savings:<name>" | "goal:<name>"
    target = db.Column(db.String(160), nullable=False)
    kind = db.Column(AllocationType, nullable=False)
    value = db.Column(db.Integer, nullable=False)  # cents if fixed, percent if percent

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(kind = 'fixed' AND value >= 0) OR (kind = 'percent' AND value BETWEEN 0 AND 100)",
            name="ck_alloc_value_semantics",
        ),
        Index("ix_allocations_scenario_kind", "scenario_id", "kind"),
    )
```

Run migration:

```bash
flask db migrate -m "add planning scenarios, bills, allocations"
flask db upgrade
```

---

## **Phase 2 — Service Layer**

Create `backend/app/services/planning_service.py`:

```python
# backend/app/services/planning_service.py
from sqlalchemy.orm import joinedload
from app.models import db, PlanningScenario, ScenarioAllocation

def get_scenario_for_user(scenario_id, user_id):
    return (
        db.session.query(PlanningScenario)
        .options(joinedload(PlanningScenario.bills), joinedload(PlanningScenario.allocations))
        .filter(PlanningScenario.id == scenario_id, PlanningScenario.user_id == user_id)
        .first()
    )

def validate_percent_cap(scenario: PlanningScenario) -> None:
    pct = sum(a.value for a in scenario.allocations if a.kind == "percent")
    if pct > 100:
        raise ValueError("Percent allocations exceed 100%")

def upsert_allocation(scenario: PlanningScenario, alloc: ScenarioAllocation) -> None:
    db.session.add(alloc)
    db.session.flush()
    validate_percent_cap(scenario)

def delete_allocation(scenario: PlanningScenario, alloc_id) -> None:
    ScenarioAllocation.query.filter_by(id=alloc_id, scenario_id=scenario.id).delete()
    db.session.flush()
    validate_percent_cap(scenario)
```

---

## **Phase 3 — Routes**

Create `backend/app/routes/planning.py`:

```python
# backend/app/routes/planning.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.exceptions import NotFound, BadRequest, Forbidden
from app.models import db, PlanningScenario, PlannedBill, ScenarioAllocation
from app.services import planning_service

bp = Blueprint("planning", __name__, url_prefix="/api/planning")


def ensure_owner(s: PlanningScenario):
    if s.user_id != current_user.id:
        raise Forbidden("Not your scenario")


@bp.get("/")
@login_required
def list_scenarios():
    q = (PlanningScenario.query
         .filter_by(user_id=current_user.id)
         .order_by(PlanningScenario.created_at.desc()))
    items = q.all()
    return jsonify([
        {"id": str(s.id), "name": s.name, "created_at": s.created_at.isoformat()}
        for s in items
    ])


@bp.post("/")
@login_required
def create_scenario():
    body = request.get_json() or {}
    name = (body.get("name") or "").strip()
    if not name:
        raise BadRequest("name required")
    s = PlanningScenario(user_id=current_user.id, name=name)
    db.session.add(s)
    db.session.commit()
    return jsonify({"id": str(s.id), "name": s.name}), 201


@bp.get("/<uuid:scenario_id>")
@login_required
def get_scenario(scenario_id):
    s = planning_service.get_scenario_for_user(scenario_id, current_user.id)
    if not s:
        raise NotFound()
    return jsonify({
        "id": str(s.id),
        "name": s.name,
        "bills": [{
            "id": str(b.id),
            "name": b.name,
            "amount_cents": b.amount_cents,
            "due_date": b.due_date.isoformat() if b.due_date else None,
            "category": b.category,
            "predicted": b.predicted,
        } for b in s.bills],
        "allocations": [{
            "id": str(a.id),
            "target": a.target,
            "kind": a.kind,
            "value": a.value,
        } for a in s.allocations],
    })


@bp.put("/<uuid:scenario_id>")
@login_required
def update_scenario(scenario_id):
    s = planning_service.get_scenario_for_user(scenario_id, current_user.id)
    if not s:
        raise NotFound()

    body = request.get_json() or {}
    s.bills.clear()
    for b in (body.get("bills") or []):
        s.bills.append(PlannedBill(
            name=b["name"].strip(),
            amount_cents=int(b["amount_cents"]),
            due_date=b.get("due_date"),
            category=b.get("category"),
            predicted=bool(b.get("predicted", False)),
        ))

    s.allocations.clear()
    for a in (body.get("allocations") or []):
        s.allocations.append(ScenarioAllocation(
            target=a["target"],
            kind=a["kind"],
            value=int(a["value"]),
        ))

    planning_service.validate_percent_cap(s)
    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/<uuid:scenario_id>")
@login_required
def delete_scenario(scenario_id):
    s = planning_service.get_scenario_for_user(scenario_id, current_user.id)
    if not s:
        raise NotFound()
    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok": True})
```

Register in `backend/app/__init__.py` alongside other blueprints.

---

## **Phase 4 — Frontend Integration**

Update `frontend/src/services/planningService.ts`:

```ts
export const planningService = {
  mode: "local" as "local" | "api",

  async listScenarios() {
    if (this.mode === "local") {
      const st = this.loadLocal();
      return st.scenarios.map((s) => ({ id: s.id, name: s.name }));
    }
    const res = await fetch("/api/planning/");
    return res.json();
  },

  async getScenario(id: string) {
    if (this.mode === "local") {
      const st = this.loadLocal();
      const s = st.scenarios.find((x) => x.id === id);
      if (!s) throw new Error("Not found");
      return {
        id: s.id,
        name: s.name,
        bills: st.bills,
        allocations: s.allocations,
      };
    }
    const res = await fetch(`/api/planning/${id}`);
    return res.json();
  },

  async putScenario(id: string, payload: { bills: any[]; allocations: any[] }) {
    if (this.mode === "local") return { ok: true };
    const res = await fetch(`/api/planning/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  loadLocal() {
    const raw = localStorage.getItem("pyNance:planning:v1");
    return raw
      ? JSON.parse(raw)
      : { scenarios: [], bills: [], allocations: [] };
  },
};
```

---

## **Phase 5 — Tests**

- **Backend**: `tests/test_api_planning.py`

  - Create scenario, add bills/allocations, enforce percent cap, ensure ownership isolation.

- **Frontend**: expand `Planning.test.tsx`:

  - CRUD flows.
  - Allocation math (fixed + percent).
  - Local vs API toggle.

---

## **Phase 6 — Docs**

- Add `docs/PLANNING-MODULE.md`.
- Cover:

  - API (`/api/planning`).
  - Frontend usage (`PlanningContext`, `planningService`).
  - Migration commands.

---

## **Phase 7 — Deployment**

- Run migrations, deploy API to staging.
- Flip frontend `planningService.mode` to `"api"`.
- Validate end-to-end: create scenario → persist in DB → reload in UI.

---

# 📌 Repo Concerns & Fit

- `models.py` is large (\~12 KB). Consider `models/planning.py` for maintainability.
- Auth: all routes must scope to `current_user`.
- Tests: repo already has strong coverage; add API tests before rollout.

---

✅ This rewrite now **fits your repo conventions** (SQLAlchemy, Flask blueprints, React/TS frontend, Vitest/RTL tests), eliminates the earlier schema mismatch (Bills vs Allocations), and enforces allocation rules in one place.
