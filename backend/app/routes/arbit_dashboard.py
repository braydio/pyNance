"""Endpoints for the experimental Arbit dashboard."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.services import arbit_metrics

arbit_dashboard = Blueprint("arbit_dashboard", __name__)


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
