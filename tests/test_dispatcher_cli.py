import importlib.util
import logging
import os
import sys
import types
from datetime import datetime, timedelta

from click.testing import CliRunner
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BASE_BACKEND)


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dispatcher_skips_by_last_refreshed(monkeypatch):
    sys.modules.pop("app", None)
    logger_stub = types.SimpleNamespace(
        info=lambda *a, **k: None,
        debug=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        error=lambda *a, **k: None,
    )
    config_stub = types.ModuleType("app.config")
    config_stub.logger = logger_stub
    sys.modules["app.config"] = config_stub

    extensions_stub = types.ModuleType("app.extensions")
    extensions_stub.db = types.SimpleNamespace(session=types.SimpleNamespace(commit=lambda: None))
    sys.modules["app.extensions"] = extensions_stub

    calls = []
    sync_stub = types.ModuleType("app.services.sync_service")
    sync_stub.sync_account = lambda acct: calls.append(acct)
    services_pkg = types.ModuleType("app.services")
    services_pkg.sync_service = sync_stub
    sys.modules["app.services"] = services_pkg
    sys.modules["app.services.sync_service"] = sync_stub
    app_pkg = types.ModuleType("app")
    app_pkg.services = services_pkg
    sys.modules["app"] = app_pkg

    models_stub = types.ModuleType("app.models")

    class DummyPlaid:
        def __init__(self, ts):
            self.access_token = "p"
            self.last_refreshed = ts

    class DummyTeller:
        def __init__(self, ts):
            self.access_token = "t"
            self.last_refreshed = ts

    class DummyAccount:
        def __init__(self, link_type, ts):
            self.link_type = link_type
            self.user_id = "u1"
            self.id = link_type
            self.plaid_account = DummyPlaid(ts) if link_type == "Plaid" else None
            self.teller_account = DummyTeller(ts) if link_type == "Teller" else None

    accounts = [
        DummyAccount("Plaid", datetime.utcnow() - timedelta(hours=1)),
        DummyAccount("Teller", datetime.utcnow() - timedelta(hours=9)),
    ]

    class Query:
        def all(self):
            return accounts

    models_stub.Account = DummyAccount
    models_stub.db = extensions_stub.db
    models_stub.Account.query = Query()
    sys.modules["app.models"] = models_stub
    sys.modules["backend.app.models"] = models_stub

    path = os.path.join(BASE_BACKEND, "app", "helpers", "account_refresh_dispatcher.py")
    dispatcher = _load_module("app.helpers.account_refresh_dispatcher", path)

    app = Flask(__name__)
    with app.app_context():
        dispatcher.refresh_all_accounts()

    assert len(calls) == 1
    assert calls[0].link_type == "Teller"


def test_sync_service_called_via_cli(monkeypatch):
    sys.modules.pop("app", None)
    dispatcher_stub = types.ModuleType("app.helpers.account_refresh_dispatcher")
    called = []
    dispatcher_stub.refresh_all_accounts = lambda: called.append(True)
    sys.modules["app.helpers.account_refresh_dispatcher"] = dispatcher_stub

    def fake_create_app():
        return Flask(__name__)

    app_pkg = types.ModuleType("app")
    app_pkg.create_app = fake_create_app
    sys.modules["app"] = app_pkg

    path = os.path.join(BASE_BACKEND, "app", "cli", "sync.py")
    cli = _load_module("app.cli.sync", path)

    runner = CliRunner()
    result = runner.invoke(cli.sync_accounts)
    assert result.exit_code == 0
    assert called == [True]

def test_sync_service_helpers():
    sys.modules.pop("app", None)
    warnings = []
    logger_stub = types.SimpleNamespace(
        info=lambda *a, **k: None,
        debug=lambda *a, **k: None,
        warning=lambda *a, **k: warnings.append("warn"),
        error=lambda *a, **k: None,
    )
    config_stub = types.ModuleType("app.config")
    config_stub.logger = logger_stub
    sys.modules["app.config"] = config_stub

    calls = []

    helpers_pkg = types.ModuleType("app.helpers")
    plaid_stub = types.ModuleType("app.helpers.plaid_helpers")
    teller_stub = types.ModuleType("app.helpers.teller_helpers")
    plaid_stub.get_accounts = lambda token, uid: calls.append(("plaid", token, uid))
    teller_stub.get_teller_accounts = lambda token, uid: calls.append(("teller", token, uid))
    helpers_pkg.plaid_helpers = plaid_stub
    helpers_pkg.teller_helpers = teller_stub
    sys.modules["app.helpers"] = helpers_pkg
    sys.modules["app.helpers.plaid_helpers"] = plaid_stub
    sys.modules["app.helpers.teller_helpers"] = teller_stub
    backend_pkg = types.ModuleType("backend")
    backend_app_pkg = types.ModuleType("backend.app")
    backend_helpers_pkg = types.ModuleType("backend.app.helpers")
    backend_helpers_pkg.plaid_helpers = plaid_stub
    backend_helpers_pkg.teller_helpers = teller_stub
    sys.modules["backend"] = backend_pkg
    sys.modules["backend.app"] = backend_app_pkg
    sys.modules["backend.app.helpers"] = backend_helpers_pkg
    sys.modules["backend.app.helpers.plaid_helpers"] = plaid_stub
    sys.modules["backend.app.helpers.teller_helpers"] = teller_stub

    models_stub = types.ModuleType("app.models")

    class DP:
        def __init__(self, token):
            self.access_token = token

    class DT:
        def __init__(self, token):
            self.access_token = token

    class DummyAccount:
        def __init__(self, link_type):
            self.id = link_type
            self.link_type = link_type
            self.user_id = "u1"
            self.plaid_account = DP("p") if link_type == "Plaid" else None
            self.teller_account = DT("t") if link_type == "Teller" else None

    sys.modules["app.models"] = models_stub
    sys.modules["backend.app.models"] = models_stub
    models_stub.Account = DummyAccount

    path = os.path.join(BASE_BACKEND, "app", "services", "sync_service.py")
    service = _load_module("app.services.sync_service", path)

    service.sync_account(DummyAccount("Plaid"))
    service.sync_account(DummyAccount("Teller"))

    log_records = []
    handler = logging.Handler()
    handler.emit = lambda record: log_records.append(record)
    service.logger.addHandler(handler)

    missing = DummyAccount("Plaid")
    missing.plaid_account = None
    service.sync_account(missing)

    assert calls[0][0] == "plaid"
    assert calls[1][0] == "teller"
    assert len(calls) == 2
    assert any("Missing PlaidAccount relation" in r.getMessage() for r in log_records)
