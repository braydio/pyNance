# backend/app/sql/planning_logic.py
"""Service layer for Planning features.

Encapsulates all business logic and DB operations for:
- PlanningScenario
- PlannedBill
- ScenarioAllocation
"""

import uuid
from datetime import date
from typing import Any, Dict, Optional

from app.extensions import db
from app.models import PlannedBill, PlanningScenario, ScenarioAllocation
from werkzeug.exceptions import BadRequest, NotFound


# -----------------------------
# Helpers
# -----------------------------
def parse_due_date(raw: Optional[str]) -> Optional[date]:
    """Parse ISO date string safely."""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise BadRequest("Invalid due_date format, must be YYYY-MM-DD")


def validate_percent_cap(scenario: PlanningScenario) -> None:
    """Ensure percent allocations sum <= 100."""
    percent_total = sum(a.value for a in scenario.allocations if a.kind == "percent")
    if percent_total > 100:
        raise BadRequest("Percent allocations cannot exceed 100%")


# -----------------------------
# CRUD Operations
# -----------------------------
def list_scenarios():
    return PlanningScenario.query.order_by(PlanningScenario.created_at.desc()).all()


def get_scenario(scenario_id: uuid.UUID) -> Optional[PlanningScenario]:
    return PlanningScenario.query.filter_by(id=scenario_id).first()


def create_scenario(name: str) -> PlanningScenario:
    if not name.strip():
        raise BadRequest("name is required")
    scenario = PlanningScenario(name=name.strip())
    db.session.add(scenario)
    db.session.commit()
    return scenario


def update_scenario(scenario_id: uuid.UUID, data: Dict[str, Any]) -> PlanningScenario:
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise NotFound("Scenario not found")

    # Clear and replace bills
    scenario.bills.clear()
    for b in data.get("bills") or []:
        try:
            amount_cents = int(b["amount_cents"])
        except (KeyError, ValueError):
            raise BadRequest("Invalid or missing amount_cents")

        bill = PlannedBill(
            name=(b.get("name") or "").strip(),
            amount_cents=amount_cents,
            due_date=parse_due_date(b.get("due_date")),
            category=b.get("category"),
            predicted=bool(b.get("predicted", False)),
        )
        if not bill.name:
            raise BadRequest("Bill name required")
        scenario.bills.append(bill)

    # Clear and replace allocations
    scenario.allocations.clear()
    for a in data.get("allocations") or []:
        kind = a.get("kind")
        if kind not in ("fixed", "percent"):
            raise BadRequest("Invalid allocation kind")

        try:
            value = int(a["value"])
        except (KeyError, ValueError):
            raise BadRequest("Invalid or missing allocation value")

        scenario.allocations.append(
            ScenarioAllocation(
                target=(a.get("target") or "").strip(),
                kind=kind,
                value=value,
            )
        )

    validate_percent_cap(scenario)
    db.session.commit()
    return scenario


def delete_scenario(scenario_id: uuid.UUID) -> None:
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise NotFound("Scenario not found")
    db.session.delete(scenario)
    db.session.commit()
