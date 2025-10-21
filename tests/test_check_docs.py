"""Tests for the documentation coverage checker."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_check_docs() -> ModuleType:
    """Dynamically load the documentation checker without relying on packages."""

    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_docs.py"
    spec = importlib.util.spec_from_file_location("scripts.check_docs", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to load check_docs module")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("scripts.check_docs", module)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


check_docs = _load_check_docs()


def test_check_file_detects_accounts_doc():
    """Known backend routes should map to existing documentation entries."""

    corpora = {
        name: check_docs.DocCorpus(path) for name, path in check_docs.DOC_ROOTS.items()
    }
    result = check_docs.check_file(Path("backend/app/routes/accounts.py"), corpora)

    assert result.is_documented
    assert result.doc_path is not None
    assert "docs/backend" in result.doc_path.as_posix()


def test_check_file_detects_component_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """CamelCase Vue components fall back to name-based matching."""

    frontend_docs = tmp_path / "frontend"
    frontend_docs.mkdir()
    doc_file = frontend_docs / "components.md"
    doc_file.write_text(
        "## SkeletonCard\n\nDetails about SkeletonCard component.\n", encoding="utf-8"
    )

    monkeypatch.setitem(check_docs.DOC_ROOTS, "frontend", frontend_docs)

    corpora = {"frontend": check_docs.DocCorpus(frontend_docs)}
    result = check_docs.check_file(
        Path("frontend/src/components/SkeletonCard.vue"), corpora
    )

    assert result.is_documented
    assert result.doc_path == doc_file


def test_filter_relevant_files_skips_non_targets():
    """Only backend/frontend Python and Vue files should be considered."""

    paths = [
        Path("backend/app/routes/accounts.py"),
        Path("frontend/src/App.vue"),
        Path("backend/README.md"),
        Path("scripts/check_docs.py"),
    ]

    filtered = check_docs.filter_relevant_files(paths)

    assert Path("backend/app/routes/accounts.py") in filtered
    assert Path("frontend/src/App.vue") in filtered
    assert Path("backend/README.md") not in filtered
    assert Path("scripts/check_docs.py") not in filtered
