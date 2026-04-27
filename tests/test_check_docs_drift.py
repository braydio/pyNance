"""Tests for documentation drift enforcement."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_check_docs_drift() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_docs_drift.py"
    spec = importlib.util.spec_from_file_location("scripts.check_docs_drift", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to load check_docs_drift module")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.check_docs_drift", module)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


check_docs_drift = _load_check_docs_drift()


def test_route_change_requires_api_or_route_docs():
    findings = check_docs_drift.check_drift([Path("backend/app/routes/planning.py")])

    assert len(findings) == 1
    assert "docs/backend/api-reference.md" in findings[0].message


def test_route_change_passes_with_api_reference_update():
    findings = check_docs_drift.check_drift(
        [
            Path("backend/app/routes/planning.py"),
            Path("docs/backend/api-reference.md"),
        ]
    )

    assert findings == []


def test_service_change_passes_with_matching_service_doc():
    findings = check_docs_drift.check_drift(
        [
            Path("backend/app/services/planning_service.py"),
            Path("docs/backend/app/services/planning_service.md"),
        ]
    )

    assert findings == []


def test_tests_do_not_require_docs():
    findings = check_docs_drift.check_drift([Path("frontend/src/views/__tests__/Settings.spec.js")])

    assert findings == []
