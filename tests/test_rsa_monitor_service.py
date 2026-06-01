"""Tests for read-only RSA runtime monitoring summaries."""

from __future__ import annotations

import csv
import importlib.util
import json
import os
from datetime import datetime

SERVICE_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "services", "rsa_monitor.py")
spec = importlib.util.spec_from_file_location("rsa_monitor_service_under_test", SERVICE_PATH)
rsa_monitor_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rsa_monitor_service)

build_rsa_monitor_status = rsa_monitor_service.build_rsa_monitor_status


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_rsa_monitor_status_summarizes_runtime_files(tmp_path, monkeypatch):
    rsassistant_root = tmp_path / "RSAssistant"
    autorsa_root = rsassistant_root / "AutoRSA-GUI.local"
    logs_root = rsassistant_root / "volumes" / "logs"
    db_root = rsassistant_root / "volumes" / "db"
    logs_root.mkdir(parents=True)
    db_root.mkdir(parents=True)
    autorsa_root.mkdir(parents=True)
    monkeypatch.setenv("RSASSISTANT_ROOT", str(rsassistant_root))
    monkeypatch.setenv("AUTORSA_GUI_ROOT", str(autorsa_root))

    (logs_root / "heartbeat.txt").write_text(datetime.now().isoformat(), encoding="utf-8")
    (logs_root / "app.log").write_text(
        "2026-05-30 12:00:00,000 - INFO - running\n"
        "2026-05-30 12:01:00,000 - WARNING - watch item\n"
        "2026-05-30 12:02:00,000 - INFO - access_token=secret-value\n",
        encoding="utf-8",
    )
    (logs_root / "rsassistant.log").write_text("2026-05-30 12:00:00,000 - INFO - bot ready\n", encoding="utf-8")
    (logs_root / "source_return.log").write_text("2026-05-30 12:00:00,000 - INFO - source ready\n", encoding="utf-8")
    _write_json(db_root / "order_queue.json", [{"ticker": "ABCD"}])
    _write_json(
        db_root / "order_send_log.json",
        [{"sent_at": "2026-05-30T12:00:00+00:00", "ticker": "ABCD", "action": "buy", "quantity": 1}],
    )
    _write_json(
        db_root / "auto_rsa_holdings.json",
        [
            {"broker": "BBAE", "account": "1234", "ticker": "ABCD", "account_total": 50},
            {"broker": "BBAE", "account": "1234", "ticker": "WXYZ", "account_total": 50},
        ],
    )
    with (autorsa_root / "account_history.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "broker", "account", "value"])
        writer.writeheader()
        writer.writerow({"timestamp": "2026-05-30T12:00:00", "broker": "BBAE", "account": "1234", "value": "50"})
        writer.writerow({"timestamp": "2026-05-30T12:00:00", "broker": "Webull", "account": "9999", "value": "25.5"})

    payload = build_rsa_monitor_status()

    assert payload["overall_status"] == "ok"
    assert payload["heartbeat"]["status"] == "ok"
    assert payload["orders"]["queue"]["count"] == 1
    assert payload["orders"]["sent"]["recent"][0]["ticker"] == "ABCD"
    assert payload["holdings"]["positions"] == 2
    assert payload["holdings"]["brokers"][0]["account_total"] == 50
    assert payload["account_history"]["total_value"] == 75.5
    assert payload["logs"][0]["warning_count"] == 1
    assert "secret-value" not in "\n".join(payload["logs"][0]["recent_lines"])


def test_build_rsa_monitor_status_degrades_when_runtime_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("RSASSISTANT_ROOT", str(tmp_path / "missing-rsassistant"))
    monkeypatch.setenv("AUTORSA_GUI_ROOT", str(tmp_path / "missing-autorsa"))

    payload = build_rsa_monitor_status()

    assert payload["overall_status"] == "degraded"
    assert payload["heartbeat"]["status"] == "missing"
    assert payload["components"][0]["status"] == "missing"
    assert payload["account_history"]["status"] == "missing"
