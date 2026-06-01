"""Read-only status summaries for local RSAssistant and AutoRSA runtimes."""

from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_RSASSISTANT_ROOT = Path.home() / "Production" / "RSAssistant"
DEFAULT_AUTORSA_GUI_ROOT = DEFAULT_RSASSISTANT_ROOT / "AutoRSA-GUI.local"
TAIL_BYTES = 64 * 1024
REDACTION_PATTERNS = (
    re.compile(r"(?i)(access[_-]?token|refresh[_-]?token|api[_-]?key|password|secret)(=|:)\S+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
)


def build_rsa_monitor_status() -> dict[str, Any]:
    """Build the complete monitor payload for the RSA production runtimes."""

    rsassistant_root = Path(os.getenv("RSASSISTANT_ROOT", DEFAULT_RSASSISTANT_ROOT)).expanduser()
    autorsa_root = Path(os.getenv("AUTORSA_GUI_ROOT", DEFAULT_AUTORSA_GUI_ROOT)).expanduser()
    logs_root = rsassistant_root / "volumes" / "logs"
    db_root = rsassistant_root / "volumes" / "db"
    heartbeat = _heartbeat_status(logs_root / "heartbeat.txt")
    components = [
        _component_status("RSAssistant", rsassistant_root, heartbeat=heartbeat),
        _component_status("AutoRSA GUI", autorsa_root),
    ]

    return {
        "generated_at": _iso_now(),
        "overall_status": _overall_status([heartbeat, *components]),
        "paths": {
            "rsassistant_root": str(rsassistant_root),
            "autorsa_gui_root": str(autorsa_root),
        },
        "components": components,
        "heartbeat": heartbeat,
        "logs": [
            _log_summary("RSAssistant app", logs_root / "app.log"),
            _log_summary("RSAssistant bot", logs_root / "rsassistant.log"),
            _log_summary("Source return", logs_root / "source_return.log"),
        ],
        "orders": _orders_summary(db_root / "order_queue.json", db_root / "order_send_log.json"),
        "holdings": _holdings_summary(db_root / "auto_rsa_holdings.json"),
        "account_history": _account_history_summary(autorsa_root / "account_history.csv"),
    }


def _iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _file_meta(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
    except OSError:
        return {"path": str(path), "exists": False, "size_bytes": 0, "modified_at": None}

    return {
        "path": str(path),
        "exists": True,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
    }


def _component_status(name: str, path: Path, heartbeat: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = _file_meta(path)
    status = "ok" if meta["exists"] else "missing"
    if heartbeat and heartbeat.get("status") == "stale":
        status = "stale"
    return {"name": name, "status": status, "root": str(path), "meta": meta}


def _heartbeat_status(path: Path) -> dict[str, Any]:
    meta = _file_meta(path)
    if not meta["exists"]:
        return {"status": "missing", "last_seen_at": None, "age_seconds": None, "meta": meta}

    raw_value = path.read_text(encoding="utf-8", errors="replace").strip()
    try:
        last_seen = datetime.fromisoformat(raw_value)
    except ValueError:
        return {"status": "unknown", "last_seen_at": raw_value, "age_seconds": None, "meta": meta}

    age_seconds = max(0, int((datetime.now(last_seen.tzinfo) - last_seen).total_seconds()))
    status = "ok" if age_seconds <= 180 else "stale"
    return {
        "status": status,
        "last_seen_at": last_seen.isoformat(timespec="seconds"),
        "age_seconds": age_seconds,
        "meta": meta,
    }


def _overall_status(items: list[dict[str, Any]]) -> str:
    statuses = {item.get("status") for item in items}
    if "missing" in statuses:
        return "degraded"
    if "stale" in statuses:
        return "stale"
    if "unknown" in statuses:
        return "unknown"
    return "ok"


def _tail_lines(path: Path, limit: int = 30) -> list[str]:
    if limit <= 0 or not path.exists():
        return []

    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        file_size = handle.tell()
        handle.seek(max(file_size - TAIL_BYTES, 0))
        chunk = handle.read().decode("utf-8", errors="replace")

    return [_redact_line(line) for line in chunk.splitlines() if line][-limit:]


def _redact_line(line: str) -> str:
    redacted = line
    for pattern in REDACTION_PATTERNS:
        redacted = pattern.sub(
            lambda match: f"{match.group(1)}{match.group(2) if len(match.groups()) > 1 else ''}[redacted]", redacted
        )
    return redacted


def _log_summary(name: str, path: Path) -> dict[str, Any]:
    meta = _file_meta(path)
    lines = _tail_lines(path)
    warning_count = sum(1 for line in lines if "WARNING" in line.upper())
    error_count = sum(1 for line in lines if "ERROR" in line.upper() or "EXCEPTION" in line.upper())
    status = "missing"
    if meta["exists"]:
        status = "error" if error_count else "warning" if warning_count else "ok"

    return {
        "name": name,
        "status": status,
        "meta": meta,
        "line_count": len(lines),
        "warning_count": warning_count,
        "error_count": error_count,
        "recent_lines": lines,
    }


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return fallback


def _orders_summary(queue_path: Path, sent_path: Path) -> dict[str, Any]:
    queue = _read_json(queue_path, {})
    sent_orders = _read_json(sent_path, [])
    queue_items = queue if isinstance(queue, list) else list(queue.values()) if isinstance(queue, dict) else []
    sent_items = sent_orders if isinstance(sent_orders, list) else []

    return {
        "queue": {
            "status": "ok" if queue_path.exists() else "missing",
            "count": len(queue_items),
            "meta": _file_meta(queue_path),
        },
        "sent": {
            "status": "ok" if sent_path.exists() else "missing",
            "count": len(sent_items),
            "meta": _file_meta(sent_path),
            "recent": [_public_order(item) for item in sent_items[-10:]],
        },
    }


def _public_order(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "sent_at": item.get("sent_at"),
        "ticker": item.get("ticker"),
        "action": item.get("action"),
        "quantity": item.get("quantity"),
        "broker": item.get("broker"),
        "command": item.get("command"),
    }


def _holdings_summary(path: Path) -> dict[str, Any]:
    rows = _read_json(path, [])
    if not isinstance(rows, list):
        rows = []

    broker_counts: dict[str, int] = defaultdict(int)
    tickers: set[str] = set()
    accounts: set[tuple[str, str]] = set()
    broker_values: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        if not isinstance(row, dict):
            continue
        broker = str(row.get("broker") or "Unknown")
        account = str(row.get("account") or "")
        ticker = str(row.get("ticker") or "")
        broker_counts[broker] += 1
        if ticker:
            tickers.add(ticker)
        if account:
            accounts.add((broker, account))
            broker_values[broker][account] = _to_float(row.get("account_total"))

    return {
        "status": "ok" if path.exists() else "missing",
        "meta": _file_meta(path),
        "positions": len(rows),
        "accounts": len(accounts),
        "tickers": len(tickers),
        "brokers": [
            {
                "name": broker,
                "positions": broker_counts[broker],
                "account_count": len(broker_values[broker]),
                "account_total": round(sum(broker_values[broker].values()), 2),
            }
            for broker in sorted(broker_counts)
        ],
    }


def _account_history_summary(path: Path) -> dict[str, Any]:
    meta = _file_meta(path)
    if not meta["exists"]:
        return {"status": "missing", "meta": meta, "latest_timestamp": None, "brokers": [], "total_value": 0}

    latest_timestamp: str | None = None
    latest_rows: list[dict[str, str]] = []
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                timestamp = row.get("timestamp")
                if not timestamp:
                    continue
                if latest_timestamp is None or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_rows = [row]
                elif timestamp == latest_timestamp:
                    latest_rows.append(row)
    except OSError:
        return {"status": "missing", "meta": meta, "latest_timestamp": None, "brokers": [], "total_value": 0}

    brokers: dict[str, dict[str, float]] = defaultdict(lambda: {"accounts": 0, "value": 0.0})
    for row in latest_rows:
        broker = row.get("broker") or "Unknown"
        brokers[broker]["accounts"] += 1
        brokers[broker]["value"] += _to_float(row.get("value"))

    broker_payload = [
        {"name": broker, "accounts": int(values["accounts"]), "value": round(values["value"], 2)}
        for broker, values in sorted(brokers.items())
    ]

    return {
        "status": "ok",
        "meta": meta,
        "latest_timestamp": latest_timestamp,
        "account_count": len(latest_rows),
        "total_value": round(sum(item["value"] for item in broker_payload), 2),
        "brokers": broker_payload,
    }


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
