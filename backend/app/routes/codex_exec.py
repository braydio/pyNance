"""Admin-only route for constrained Codex command execution."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.codex_exec_service import (
    CodexExecAuthorizationError,
    CodexExecValidationError,
    ensure_admin_authorized,
    execute_task,
    log_exec_audit,
    validate_task,
)

codex_exec = Blueprint("codex_exec", __name__)


@codex_exec.route("/exec", methods=["POST"])
def execute_codex_task():
    """Run a validated Codex task using strict command and auth controls."""

    requester = request.headers.get("X-Requester", "unknown")
    preset = None
    task = ""

    try:
        ensure_admin_authorized(request.headers.get("X-Admin-Token"))
    except CodexExecAuthorizationError as exc:
        log_exec_audit(requester=requester, task="", preset=None, status="unauthorized")
        return jsonify({"status": "error", "error": str(exc)}), 403

    payload = request.get_json(silent=True) or {}
    preset = payload.get("preset")

    try:
        task = validate_task(payload.get("task"))
    except CodexExecValidationError as exc:
        log_exec_audit(requester=requester, task="", preset=preset if isinstance(preset, str) else None, status="invalid")
        return jsonify({"status": "error", "error": str(exc)}), 400

    result = execute_task(task)
    log_exec_audit(requester=requester, task=task, preset=preset if isinstance(preset, str) else None, status=result.status)

    if result.status == "timeout":
        return jsonify({"status": "error", "error": "command timed out", "stdout": result.stdout, "stderr": result.stderr}), 504
    if result.status == "execution_unavailable":
        return jsonify({"status": "error", "error": "execution backend unavailable"}), 503
    if result.status == "failed":
        return (
            jsonify({"status": "error", "error": "command failed", "stdout": result.stdout, "stderr": result.stderr}),
            500,
        )

    return jsonify({"status": "success", "stdout": result.stdout, "stderr": result.stderr}), 200
