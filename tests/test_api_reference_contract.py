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
    assert "take precedence over `range`" in section
    assert "does not override either bound" in section
    assert "`range` is still parsed in every case" in section
    assert "Accepted path identifier formats" in section
    assert "External `account_id` string" in section
    assert "Internal numeric primary key" in section
    assert "`/api/accounts/acc_12345/history`" in section
    assert "`/api/accounts/42/history`" in section
    assert '"balances"' in section
    assert '"history"' in section
    assert "legacy alias" in section


def test_api_reference_has_balanced_markdown_fences_in_accounts_history_neighborhood():
    """Surrounding endpoint listings should retain valid fenced code blocks."""

    doc_text = _read(DOC_PATH)

    shared_start = "### 🔸 Shared Resources"
    provider_end = "**POST /api/plaid/transactions/refresh_accounts**"
    start_index = doc_text.index(shared_start)
    end_index = doc_text.index(provider_end)
    neighborhood = doc_text[start_index:end_index]

    assert "```text\nGET    /api/transactions/get_transactions" in neighborhood
    assert "```text\nPOST   /api/plaid/transactions/exchange_public_token" in neighborhood

    fence_lines = [line.strip() for line in neighborhood.splitlines() if line.strip().startswith("```")]
    opened = sum(1 for line in fence_lines if line != "```")
    closed = fence_lines.count("```")
    assert opened == closed


def test_accounts_history_docs_match_route_contract_markers():
    """Route source should still expose the documented request and response knobs."""

    route_source = _read(ROUTE_PATH)

    assert 'request.args.get("range", "30d")' in route_source
    assert 'request.args.get("start_date")' in route_source
    assert 'request.args.get("end_date")' in route_source
    assert 'response_payload["history"] = response_payload["balances"]' in route_source
    assert "resolve_account_by_any_id" in route_source
