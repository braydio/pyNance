"""Unit tests for item-scoped cursor persistence in Plaid sync."""

from types import SimpleNamespace

from app.services import plaid_sync


class _FakeColumn:
    def in_(self, values):
        return values


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


class _FakeTransactionsSyncRequest:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class _FakeAccountQuery:
    def __init__(self, accounts):
        self._accounts = accounts
        self._filters = {}

    def filter_by(self, **kwargs):
        self._filters = kwargs
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        account_id = self._filters.get("account_id")
        for account in self._accounts:
            if account.account_id == account_id:
                return account
        return None

    def all(self):
        return list(self._accounts)


class _FakePlaidAccountQuery:
    def __init__(self, plaid_accounts):
        self._plaid_accounts = plaid_accounts
        self._filters = {}

    def filter_by(self, **kwargs):
        self._filters = kwargs
        return self

    def first(self):
        for plaid_account in self._plaid_accounts:
            if all(getattr(plaid_account, key) == value for key, value in self._filters.items()):
                return plaid_account
        return None

    def all(self):
        return [
            plaid_account
            for plaid_account in self._plaid_accounts
            if all(getattr(plaid_account, key) == value for key, value in self._filters.items())
        ]


class _FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _FakePlaidClient:
    def __init__(self, payload):
        self._payload = payload

    def transactions_sync(self, _req):
        return _FakeResponse(self._payload)


def test_sync_account_transactions_persists_item_cursor_once(monkeypatch):
    """Final cursor persistence should run once for all Plaid accounts in the item."""

    account = SimpleNamespace(account_id="acc-1", user_id="user-1")
    plaid_accounts = [
        SimpleNamespace(
            account_id="acc-1",
            item_id="item-1",
            access_token="token",
            sync_cursor="cursor-0",
            last_refreshed=None,
        ),
        SimpleNamespace(
            account_id="acc-2",
            item_id="item-1",
            access_token="token",
            sync_cursor=None,
            last_refreshed=None,
        ),
    ]

    fake_session = _FakeSession()
    monkeypatch.setattr(plaid_sync, "db", SimpleNamespace(session=fake_session))
    monkeypatch.setattr(plaid_sync, "ensure_transactions_sequence", lambda: None)
    monkeypatch.setattr(plaid_sync, "_upsert_transaction", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(plaid_sync, "_apply_removed", lambda removed: len(removed))
    monkeypatch.setattr(
        plaid_sync,
        "plaid_client",
        _FakePlaidClient(
            {
                "added": [],
                "modified": [],
                "removed": [],
                "next_cursor": "cursor-1",
                "has_more": False,
            }
        ),
    )
    monkeypatch.setattr(plaid_sync, "TransactionsSyncRequest", _FakeTransactionsSyncRequest)

    fake_account_cls = SimpleNamespace(query=_FakeAccountQuery([account]), account_id=_FakeColumn())
    fake_plaid_cls = SimpleNamespace(query=_FakePlaidAccountQuery(plaid_accounts))
    monkeypatch.setattr(plaid_sync, "Account", fake_account_cls)
    monkeypatch.setattr(plaid_sync, "PlaidAccount", fake_plaid_cls)

    result = plaid_sync.sync_account_transactions("acc-1")

    assert result["next_cursor"] == "cursor-1"
    assert fake_session.commits == 2
    assert fake_session.rollbacks == 0
    assert all(pa.sync_cursor == "cursor-1" for pa in plaid_accounts)
    assert all(pa.last_refreshed is not None for pa in plaid_accounts)
