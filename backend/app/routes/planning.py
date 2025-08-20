# backend/app/routes/planning.py
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest
from app.models import db, PlanningScenario, PlannedBill, ScenarioAllocation
from app.services import planning_service

bp = Blueprint("planning", __name__, url_prefix="/api/planning")


@bp.get("/")
def list_scenarios():
    items = PlanningScenario.query.order_by(PlanningScenario.created_at.desc()).all()
    return jsonify(
        [
            {"id": str(s.id), "name": s.name, "created_at": s.created_at.isoformat()}
            for s in items
        ]
    )


@bp.post("/")
def create_scenario():
    body = request.get_json() or {}
    name = (body.get("name") or "").strip()
    if not name:
        raise BadRequest("name required")
    s = PlanningScenario(name=name)
    db.session.add(s)
    db.session.commit()
    return jsonify({"id": str(s.id), "name": s.name}), 201


@bp.get("/<uuid:scenario_id>")
def get_scenario(scenario_id):
    s = planning_service.get_scenario(scenario_id)
    if not s:
        raise NotFound()
    return jsonify(
        {
            "id": str(s.id),
            "name": s.name,
            "bills": [
                {
                    "id": str(b.id),
                    "name": b.name,
                    "amount_cents": b.amount_cents,
                    "due_date": b.due_date.isoformat() if b.due_date else None,
                    "category": b.category,
                    "predicted": b.predicted,
                }
                for b in s.bills
            ],
            "allocations": [
                {
                    "id": str(a.id),
                    "target": a.target,
                    "kind": a.kind,
                    "value": a.value,
                }
                for a in s.allocations
            ],
        }
    )


@bp.put("/<uuid:scenario_id>")
def update_scenario(scenario_id):
    s = planning_service.get_scenario(scenario_id)
    if not s:
        raise NotFound()

    body = request.get_json() or {}
    s.bills.clear()
    for b in body.get("bills") or []:
        s.bills.append(
            PlannedBill(
                name=b["name"].strip(),
                amount_cents=int(b["amount_cents"]),
                due_date=b.get("due_date"),
                category=b.get("category"),
                predicted=bool(b.get("predicted", False)),
            )
        )

    s.allocations.clear()
    for a in body.get("allocations") or []:
        s.allocations.append(
            ScenarioAllocation(
                target=a["target"],
                kind=a["kind"],
                value=int(a["value"]),
            )
        )

    planning_service.validate_percent_cap(s)
    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/<uuid:scenario_id>")
def delete_scenario(scenario_id):
    s = planning_service.get_scenario(scenario_id)
    if not s:
        raise NotFound()
    db.session.delete(s)
    db.session.commit()
    return jsonify({"ok": True})
