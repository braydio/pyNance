"""API endpoints for managing user financial goals."""

from datetime import datetime

from app.extensions import db
from app.models import FinancialGoal
from flask import Blueprint, jsonify, request


goals = Blueprint("goals", __name__)


@goals.route("", methods=["GET"])
def list_goals():
    """Return all financial goals."""
    goals_q = FinancialGoal.query.all()
    data = [
        {
            "id": g.id,
            "user_id": g.user_id,
            "account_id": g.account_id,
            "name": g.name,
            "target_amount": g.target_amount,
            "due_date": g.due_date.isoformat(),
            "notes": g.notes,
        }
        for g in goals_q
    ]
    return jsonify({"status": "success", "data": data}), 200


@goals.route("", methods=["POST"])
def create_goal():
    """Create a new financial goal."""
    data = request.get_json() or {}
    try:
        goal = FinancialGoal(
            user_id=data.get("user_id"),
            account_id=data["account_id"],
            name=data.get("name", "Goal"),
            target_amount=float(data.get("target_amount", 0)),
            due_date=datetime.strptime(data["due_date"], "%Y-%m-%d").date(),
            notes=data.get("notes"),
        )
    except (KeyError, ValueError) as exc:  # pragma: no cover - defensive
        return jsonify({"error": str(exc)}), 400

    db.session.add(goal)
    db.session.commit()
    return jsonify({"status": "success", "id": goal.id}), 201
