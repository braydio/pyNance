"""SQL-backed service for planning bills, scenarios, and allocations."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from werkzeug.exceptions import BadRequest, NotFound

from app.extensions import db
from app.models import PlannedBill, PlanningScenario, ScenarioAllocation

VALID_FREQUENCIES = {"once", "weekly", "monthly", "yearly"}
VALID_ORIGINS = {"manual", "predicted"}
VALID_ALLOCATION_KINDS = {"fixed", "percent"}


def _coerce_uuid(raw: str, label: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(raw))
    except (TypeError, ValueError) as exc:
        raise BadRequest(f"Invalid {label}") from exc


def _parse_due_date(raw: Any) -> date | None:
    if raw in (None, ""):
        return None
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw))
    except ValueError as exc:
        raise BadRequest("Invalid dueDate; expected YYYY-MM-DD") from exc


def _require_name(data: dict[str, Any], field: str = "name") -> str:
    value = str(data.get(field, "")).strip()
    if not value:
        raise BadRequest(f"{field} is required")
    return value


def _coerce_int(data: dict[str, Any], field: str, *, default: int | None = None) -> int:
    raw = data.get(field, default)
    if raw is None:
        raise BadRequest(f"{field} is required")
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise BadRequest(f"{field} must be an integer") from exc


def _scenario_or_404(scenario_id: str) -> PlanningScenario:
    scenario = db.session.get(PlanningScenario, _coerce_uuid(scenario_id, "scenario id"))
    if scenario is None:
        raise NotFound("Scenario not found")
    return scenario


def _bill_or_404(bill_id: str) -> PlannedBill:
    bill = db.session.get(PlannedBill, _coerce_uuid(bill_id, "bill id"))
    if bill is None:
        raise NotFound("Bill not found")
    return bill


def _allocation_or_404(allocation_id: str) -> ScenarioAllocation:
    allocation = db.session.get(ScenarioAllocation, _coerce_uuid(allocation_id, "allocation id"))
    if allocation is None:
        raise NotFound("Allocation not found")
    return allocation


def _serialize_bill(bill: PlannedBill) -> dict[str, Any]:
    return {
        "id": str(bill.id),
        "name": bill.name,
        "amountCents": bill.amount_cents,
        "dueDate": bill.due_date.isoformat() if bill.due_date else "",
        "frequency": bill.frequency,
        "category": bill.category,
        "origin": bill.origin,
        "accountId": bill.account_id or bill.scenario.account_id or "",
        "scenarioId": str(bill.scenario_id),
    }


def _serialize_allocation(allocation: ScenarioAllocation) -> dict[str, Any]:
    return {
        "id": str(allocation.id),
        "target": allocation.target,
        "kind": allocation.kind,
        "value": allocation.value,
    }


def _serialize_scenario(scenario: PlanningScenario) -> dict[str, Any]:
    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "planningBalanceCents": scenario.planning_balance_cents,
        "allocations": [_serialize_allocation(allocation) for allocation in scenario.allocations],
        "accountId": scenario.account_id or "",
        "currencyCode": scenario.currency_code,
    }


def _apply_bill_fields(bill: PlannedBill, data: dict[str, Any], *, partial: bool = False) -> None:
    if not partial or "name" in data:
        bill.name = _require_name(data)

    if not partial or "amountCents" in data:
        amount_cents = _coerce_int(data, "amountCents")
        if amount_cents < 0:
            raise BadRequest("amountCents must be non-negative")
        bill.amount_cents = amount_cents

    if "dueDate" in data or not partial:
        bill.due_date = _parse_due_date(data.get("dueDate"))

    if "frequency" in data or not partial:
        frequency = data.get("frequency", "monthly")
        if frequency not in VALID_FREQUENCIES:
            raise BadRequest("frequency must be one of once, weekly, monthly, yearly")
        bill.frequency = frequency

    if "origin" in data or not partial:
        origin = data.get("origin", "manual")
        if origin not in VALID_ORIGINS:
            raise BadRequest("origin must be manual or predicted")
        bill.origin = origin
        bill.predicted = origin == "predicted"

    if "category" in data or not partial:
        bill.category = data.get("category") or None

    if "accountId" in data or not partial:
        bill.account_id = data.get("accountId") or None


def _build_allocation(data: dict[str, Any]) -> ScenarioAllocation:
    target = _require_name(data, "target")
    kind = data.get("kind")
    if kind not in VALID_ALLOCATION_KINDS:
        raise BadRequest("kind must be fixed or percent")
    value = _coerce_int(data, "value")
    if kind == "fixed" and value < 0:
        raise BadRequest("fixed allocation value must be non-negative")
    if kind == "percent" and not 0 <= value <= 100:
        raise BadRequest("percent allocation value must be between 0 and 100")
    return ScenarioAllocation(target=target, kind=kind, value=value)


def _validate_percent_cap(allocations: list[ScenarioAllocation]) -> None:
    total = sum(allocation.value for allocation in allocations if allocation.kind == "percent")
    if total > 100:
        raise BadRequest("Percent allocations cannot exceed 100%")


def list_scenarios() -> list[dict[str, Any]]:
    scenarios = PlanningScenario.query.order_by(PlanningScenario.created_at.desc()).all()
    return [_serialize_scenario(scenario) for scenario in scenarios]


def create_scenario(data: dict[str, Any]) -> dict[str, Any]:
    scenario = PlanningScenario(
        name=_require_name(data),
        account_id=data.get("accountId") or None,
        planning_balance_cents=_coerce_int(data, "planningBalanceCents", default=0),
        currency_code=(data.get("currencyCode") or "USD").upper(),
    )
    db.session.add(scenario)
    db.session.commit()
    return _serialize_scenario(scenario)


def get_bills() -> list[dict[str, Any]]:
    bills = PlannedBill.query.order_by(PlannedBill.name.asc()).all()
    return [_serialize_bill(bill) for bill in bills]


def create_bill(data: dict[str, Any]) -> dict[str, Any]:
    scenario_id = data.get("scenarioId")
    scenario = _scenario_or_404(scenario_id) if scenario_id else _ensure_default_scenario(data)
    bill = PlannedBill(scenario=scenario)
    _apply_bill_fields(bill, data)
    db.session.add(bill)
    db.session.commit()
    return _serialize_bill(bill)


def update_bill(bill_id: str, data: dict[str, Any]) -> dict[str, Any]:
    bill = _bill_or_404(bill_id)
    _apply_bill_fields(bill, data, partial=True)
    db.session.commit()
    return _serialize_bill(bill)


def delete_bill(bill_id: str) -> None:
    bill = _bill_or_404(bill_id)
    db.session.delete(bill)
    db.session.commit()


def get_allocations(scenario_id: str) -> list[dict[str, Any]]:
    scenario = _scenario_or_404(scenario_id)
    return [_serialize_allocation(allocation) for allocation in scenario.allocations]


def create_allocation(scenario_id: str, data: dict[str, Any]) -> dict[str, Any]:
    scenario = _scenario_or_404(scenario_id)
    allocation = _build_allocation(data)
    _validate_percent_cap([*scenario.allocations, allocation])
    allocation.scenario = scenario
    db.session.add(allocation)
    db.session.commit()
    return _serialize_allocation(allocation)


def update_allocation(scenario_id: str, allocation_id: str, data: dict[str, Any]) -> dict[str, Any]:
    scenario = _scenario_or_404(scenario_id)
    allocation = _allocation_or_404(allocation_id)
    if allocation.scenario_id != scenario.id:
        raise NotFound("Allocation not found")

    next_allocation = _build_allocation({**_serialize_allocation(allocation), **data})
    allocation.target = next_allocation.target
    allocation.kind = next_allocation.kind
    allocation.value = next_allocation.value
    _validate_percent_cap(list(scenario.allocations))
    db.session.commit()
    return _serialize_allocation(allocation)


def delete_allocation(scenario_id: str, allocation_id: str) -> None:
    scenario = _scenario_or_404(scenario_id)
    allocation = _allocation_or_404(allocation_id)
    if allocation.scenario_id != scenario.id:
        raise NotFound("Allocation not found")
    db.session.delete(allocation)
    db.session.commit()


def replace_allocations(scenario_id: str, allocations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenario = _scenario_or_404(scenario_id)
    next_allocations = [_build_allocation(allocation) for allocation in allocations]
    _validate_percent_cap(next_allocations)
    scenario.allocations.clear()
    scenario.allocations.extend(next_allocations)
    db.session.commit()
    return [_serialize_allocation(allocation) for allocation in scenario.allocations]


def _ensure_default_scenario(data: dict[str, Any]) -> PlanningScenario:
    scenario = PlanningScenario(
        name="Baseline plan",
        account_id=data.get("accountId") or None,
        planning_balance_cents=0,
        currency_code="USD",
    )
    db.session.add(scenario)
    db.session.flush()
    return scenario
