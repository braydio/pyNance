"""API routes for local RSAssistant and AutoRSA runtime monitoring."""

from flask import Blueprint, jsonify

from app.config import logger
from app.services.rsa_monitor import build_rsa_monitor_status

rsa_monitor = Blueprint("rsa_monitor", __name__)


@rsa_monitor.route("/status", methods=["GET"])
def get_rsa_monitor_status():
    """Return read-only monitor data for the local RSA runtimes."""

    try:
        return jsonify({"status": "success", "data": build_rsa_monitor_status()}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to build RSA monitor status: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500
