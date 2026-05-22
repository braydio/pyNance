"""Service helpers for safely executing constrained Codex commands."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.config import logger

MAX_TASK_LENGTH = 400
MAX_OUTPUT_CHARS = 8000
EXEC_TIMEOUT_SECONDS = 15
_ALLOWED_TASK_PATTERN = re.compile(r"^[A-Za-z0-9 _.,:@/+-]+$")


class CodexExecValidationError(ValueError):
    """Raised when the request payload or task content is invalid."""


class CodexExecAuthorizationError(PermissionError):
    """Raised when admin authorization checks fail."""


@dataclass(frozen=True)
class CodexExecResult:
    """Structured result for a safe Codex execution request."""

    status: str
    command: list[str]
    stdout: str
    stderr: str
    return_code: int | None


def validate_task(task: Any) -> str:
    """Validate and normalize a task string for safe command construction."""

    if not isinstance(task, str):
        raise CodexExecValidationError("task must be a string")

    normalized = task.strip()
    if not normalized:
        raise CodexExecValidationError("task must not be empty")
    if len(normalized) > MAX_TASK_LENGTH:
        raise CodexExecValidationError(f"task exceeds max length of {MAX_TASK_LENGTH}")
    if not _ALLOWED_TASK_PATTERN.fullmatch(normalized):
        raise CodexExecValidationError("task contains disallowed characters")

    return normalized


def ensure_admin_authorized(admin_token: str | None) -> None:
    """Require an explicit admin token to execute privileged commands."""

    configured_token = os.getenv("CODEX_EXEC_ADMIN_TOKEN", "").strip()
    provided = (admin_token or "").strip()
    if not configured_token or provided != configured_token:
        raise CodexExecAuthorizationError("admin authorization required")


def build_command(task: str) -> list[str]:
    """Build the only approved command shape from validated task input."""

    return ["codex", "exec", task]


def _bounded_text(value: str | None, limit: int = MAX_OUTPUT_CHARS) -> str:
    text = value or ""
    return text[:limit]


def execute_task(task: str) -> CodexExecResult:
    """Execute a validated Codex task with bounded runtime and output."""

    command = build_command(task)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CodexExecResult(
            status="timeout",
            command=command,
            stdout=_bounded_text(exc.stdout),
            stderr=_bounded_text(exc.stderr),
            return_code=None,
        )
    except OSError:
        return CodexExecResult(
            status="execution_unavailable",
            command=command,
            stdout="",
            stderr="codex executable not available",
            return_code=None,
        )

    status = "success" if completed.returncode == 0 else "failed"
    return CodexExecResult(
        status=status,
        command=command,
        stdout=_bounded_text(completed.stdout),
        stderr=_bounded_text(completed.stderr),
        return_code=completed.returncode,
    )


def log_exec_audit(*, requester: str, task: str, preset: str | None, status: str) -> None:
    """Emit structured audit logs without exposing raw task content."""

    task_hash = hashlib.sha256(task.encode("utf-8")).hexdigest()
    preset_hash = hashlib.sha256((preset or "").encode("utf-8")).hexdigest() if preset else None
    payload = {
        "event": "codex_exec",
        "requester": requester,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_hash": task_hash,
        "preset_hash": preset_hash,
        "status": status,
    }
    logger.info("codex_exec_audit %s", payload)
