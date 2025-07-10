"""CRUD endpoints for managing transaction rules."""

from app.extensions import db
from app.models import TransactionRule
from app.sql import transaction_rules_logic
from flask import Blueprint, jsonify, request

rules = Blueprint("rules", __name__)


@rules.route("/", methods=["GET"])
def list_rules():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400
    rows = transaction_rules_logic.get_applicable_rules(user_id)
    data = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "match_criteria": r.match_criteria,
            "action": r.action,
            "is_active": r.is_active,
        }
        for r in rows
    ]
    return jsonify({"status": "success", "data": data})


@rules.route("/", methods=["POST"])
def create_rule():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400
    rule = transaction_rules_logic.create_rule(
        user_id=user_id,
        match_criteria=data.get("match_criteria", {}),
        action=data.get("action", {}),
    )
    return jsonify({"status": "success", "data": {"id": rule.id}})


@rules.route("/<int:rule_id>", methods=["PATCH"])
def update_rule(rule_id: int):
    rule = TransactionRule.query.get(rule_id)
    if not rule:
        return jsonify({"status": "error", "message": "Rule not found"}), 404
    data = request.get_json() or {}
    if "match_criteria" in data:
        rule.match_criteria = data["match_criteria"]
    if "action" in data:
        rule.action = data["action"]
    if "is_active" in data:
        rule.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify({"status": "success"})


@rules.route("/<int:rule_id>", methods=["DELETE"])
def delete_rule(rule_id: int):
    rule = TransactionRule.query.get(rule_id)
    if not rule:
        return jsonify({"status": "error", "message": "Rule not found"}), 404
    db.session.delete(rule)
    db.session.commit()
    return jsonify({"status": "success"})
