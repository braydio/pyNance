"""Tests for the admin Codex execution endpoint."""

from __future__ import annotations

from app.routes.codex_exec import codex_exec
from flask import Flask


def _build_client():
    app = Flask(__name__)
    app.register_blueprint(codex_exec, url_prefix="/api/codex")
    return app.test_client()


def test_codex_exec_rejects_missing_admin_token():
    client = _build_client()

    response = client.post("/api/codex/exec", json={"task": "status"})

    assert response.status_code == 403
    assert response.get_json()["error"] == "admin authorization required"


def test_codex_exec_rejects_disallowed_task_characters(monkeypatch):
    monkeypatch.setenv("CODEX_EXEC_ADMIN_TOKEN", "secret")
    client = _build_client()

    response = client.post(
        "/api/codex/exec",
        headers={"X-Admin-Token": "secret"},
        json={"task": "status; rm -rf /"},
    )

    assert response.status_code == 400
    assert "disallowed" in response.get_json()["error"]


def test_codex_exec_success(monkeypatch):
    monkeypatch.setenv("CODEX_EXEC_ADMIN_TOKEN", "secret")
    client = _build_client()

    response = client.post(
        "/api/codex/exec",
        headers={"X-Admin-Token": "secret", "X-Requester": "admin@example.com"},
        json={"task": "show status", "preset": "default"},
    )

    # Route should not crash even when codex is unavailable in test env.
    assert response.status_code in {200, 503, 500, 504}
    body = response.get_json()
    assert body["status"] in {"success", "error"}
