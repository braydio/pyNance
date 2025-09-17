"""Dashboard-specific API routes."""

from flask import Blueprint, jsonify, request

from app.config import logger
from app.services.account_snapshot import (
    DEFAULT_USER_SCOPE,
    build_snapshot_payload,
    update_snapshot_selection,
)

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/account_snapshot", methods=["GET"])
def get_account_snapshot():
    """Return stored snapshot preferences and hydrated account data."""
    user_id = request.args.get("user_id") or DEFAULT_USER_SCOPE
    try:
        data = build_snapshot_payload(user_id=user_id)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to load account snapshot preferences: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account_snapshot", methods=["PUT"])
def update_account_snapshot():
    """Persist a new snapshot selection."""
    payload = request.get_json(silent=True) or {}
    user_id = (
        payload.get("user_id")
        or request.args.get("user_id")
        or DEFAULT_USER_SCOPE
    )
    selected_ids = payload.get("selected_account_ids")

    if selected_ids is None:
        return (
            jsonify({"status": "error", "message": "selected_account_ids is required"}),
            400,
        )
    if not isinstance(selected_ids, list):
        return (
            jsonify({"status": "error", "message": "selected_account_ids must be a list"}),
            400,
        )

    try:
        data = update_snapshot_selection(selected_ids, user_id=user_id)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to update account snapshot preferences: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500
