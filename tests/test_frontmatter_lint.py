"""Unit tests for the documentation front matter linter."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, ROOT.as_posix())

from scripts.frontmatter_lint import lint_file, parse_front_matter


@pytest.fixture()
def valid_doc(tmp_path: Path) -> Path:
    """Create a Markdown document with valid front matter."""

    doc = tmp_path / "doc.md"
    doc.write_text(
        """---
Owner: Backend Team
Last Updated: 2025-11-24
Status: Active
---

Body
""",
        encoding="utf-8",
    )
    return doc


def test_parse_front_matter_extracts_fields(valid_doc: Path) -> None:
    """Front matter parsing should pull required keys."""

    text = valid_doc.read_text(encoding="utf-8")
    result = parse_front_matter(text)

    assert result == {
        "Owner": "Backend Team",
        "Last Updated": "2025-11-24",
        "Status": "Active",
    }


def test_lint_file_passes_valid_front_matter(valid_doc: Path) -> None:
    """A well-formed document should pass the lint check."""

    result = lint_file(valid_doc, max_age_days=365)

    assert result.passed is True
    assert result.message is None


def test_lint_file_flags_missing_front_matter(tmp_path: Path) -> None:
    """Documents without a block should fail validation."""

    doc = tmp_path / "doc.md"
    doc.write_text("# Header only\n", encoding="utf-8")

    result = lint_file(doc, max_age_days=365)

    assert result.passed is False
    assert "missing front matter" in (result.message or "")


def test_lint_file_flags_stale_last_updated(valid_doc: Path) -> None:
    """Old timestamps should be reported as stale."""

    doc_text = valid_doc.read_text(encoding="utf-8").replace("2025-11-24", "2020-01-01")
    valid_doc.write_text(doc_text, encoding="utf-8")

    result = lint_file(valid_doc, max_age_days=365)

    assert result.passed is False
    assert "older than" in (result.message or "")


def test_lint_file_handles_invalid_date(valid_doc: Path) -> None:
    """Invalid dates should surface a helpful error."""

    doc_text = valid_doc.read_text(encoding="utf-8").replace("2025-11-24", "01-01-2020")
    valid_doc.write_text(doc_text, encoding="utf-8")

    result = lint_file(valid_doc, max_age_days=365)

    assert result.passed is False
    assert "invalid" in (result.message or "")
