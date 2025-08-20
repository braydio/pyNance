# backend/app/routes/planning.py
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, NotFound

from app.sql import planning_logic as logic

bp = Blueprint("planning", __name__, url_prefix="/api/planning")


@bp.get("/")
def list_scenarios():
    scenarios = logic.list_scenarios()
    return jsonify(
        [
            {"id": str(s.id), "name": s.name, "created_at": s.created_at.isoformat()}
            for s in scenarios
        ]
    )


@bp.post("/")
def create_scenario():
    body = request.get_json() or {}
    name = (body.get("name") or "").strip()
    if not name:
        raise BadRequest("name required")
    scenario = logic.create_scenario(name)
    return jsonify({"id": str(scenario.id), "name": scenario.name}), 201


@bp.get("/<uuid:scenario_id>")
def get_scenario(scenario_id):
    s = logic.get_scenario(scenario_id)
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
    body = request.get_json() or {}
    updated = logic.update_scenario(scenario_id, body)
    return jsonify({"id": str(updated.id), "ok": True})


@bp.delete("/<uuid:scenario_id>")
def delete_scenario(scenario_id):
    logic.delete_scenario(scenario_id)
    return jsonify({"ok": True})
