"""Endpoints for the experimental Arbit dashboard."""

from __future__ import annotations

from app.services import arbit_cli, arbit_metrics
from flask import Blueprint, current_app, jsonify, request

arbit_dashboard = Blueprint("arbit_dashboard", __name__)


def _parse_threshold_fee(data: dict) -> tuple[float, float] | None:
    """Validate and extract threshold and fee values from request data."""
    try:
        threshold = float(data["threshold"])
        fee = float(data["fee"])
    except (KeyError, TypeError, ValueError):
        return None
    if threshold <= 0 or fee < 0:
        return None
    return threshold, fee


@arbit_dashboard.route("/status", methods=["GET"])
def get_status():
    """Return whether the dashboard is running and its config."""
    enabled = current_app.config.get("ENABLE_ARBIT_DASHBOARD", False)
    config = {
        "arbit_exporter_url": current_app.config.get("ARBIT_EXPORTER_URL"),
        "enable_arbit_dashboard": enabled,
    }
    return jsonify({"running": enabled, "config": config}), 200


@arbit_dashboard.route("/metrics", methods=["GET"])
def metrics():
    """Return metrics from the Arbit exporter."""
    data = arbit_metrics.get_metrics()
    return jsonify(data), 200


@arbit_dashboard.route("/opportunities", methods=["GET"])
def opportunities():
    """Placeholder for opportunity data."""
    return jsonify([]), 200


@arbit_dashboard.route("/trades", methods=["GET"])
def trades():
    """Placeholder for trade data."""
    return jsonify([]), 200


@arbit_dashboard.route("/start", methods=["POST"])
def start_arbit():
    """Start the Arbit CLI process."""
    data = request.get_json(silent=True) or {}
    parsed = _parse_threshold_fee(data)
    if not parsed:
        return jsonify({"error": "Invalid threshold or fee"}), 400
    threshold, fee = parsed
    result = arbit_cli.start(threshold, fee)
    return (
        jsonify(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        ),
        200,
    )


@arbit_dashboard.route("/stop", methods=["POST"])
def stop_arbit():
    """Stop the Arbit CLI process."""
    result = arbit_cli.stop()
    return (
        jsonify(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        ),
        200,
    )


@arbit_dashboard.route("/config/update", methods=["POST"])
def update_config():
    """Update configuration for the Arbit CLI process."""
    data = request.get_json(silent=True) or {}
    parsed = _parse_threshold_fee(data)
    if not parsed:
        return jsonify({"error": "Invalid threshold or fee"}), 400
    threshold, fee = parsed
    result = arbit_cli.update_config(threshold, fee)
    return (
        jsonify(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        ),
        200,
    )
