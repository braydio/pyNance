"""Contract checks to keep API reference content aligned with route behavior."""

from pathlib import Path

DOC_PATH = Path("docs/backend/api-reference.md")
ROUTE_PATH = Path("backend/app/routes/accounts.py")


def _read(path: Path) -> str:
    """Return UTF-8 text for a repository file used by contract checks."""

    return path.read_text(encoding="utf-8")


def _history_section(doc_text: str) -> str:
    """Extract the `/api/accounts/<id>/history` section from the API reference."""

    start = "**GET /api/accounts/<id>/history**"
    end = "**GET /api/accounts/<account_id>/net_changes**"
    start_index = doc_text.index(start)
    end_index = doc_text.index(end)
    return doc_text[start_index:end_index]


def test_accounts_history_docs_capture_query_precedence_and_response_alias():
    """The API reference should document date precedence and response aliasing."""

    section = _history_section(_read(DOC_PATH))

    assert "`start_date`" in section
    assert "`end_date`" in section
    assert "`range`" in section
    assert "Precedence and window resolution rules" in section
    assert "Accepted path identifier formats" in section
    assert "External `account_id` string" in section
    assert "Internal numeric primary key" in section
    assert '"balances"' in section
    assert '"history"' in section
    assert "legacy alias" in section


def test_accounts_history_docs_match_route_contract_markers():
    """Route source should still expose the documented request and response knobs."""

    route_source = _read(ROUTE_PATH)

    assert 'request.args.get("range", "30d")' in route_source
    assert 'request.args.get("start_date")' in route_source
    assert 'request.args.get("end_date")' in route_source
    assert 'response_payload["history"] = response_payload["balances"]' in route_source
    assert "resolve_account_by_any_id" in route_source
