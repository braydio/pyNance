import importlib.util
import json
import os
import sys
import types

import pytest


def load_plaid_helpers(tmp_path):
    """Load plaid_helpers with stubs and return module and token path."""
    config_stub = types.ModuleType("app.config")
    token_path = os.path.join(tmp_path, "tokens.json")
    config_stub.FILES = {
        "PLAID_TOKENS": token_path,
        "LAST_TX_REFRESH": os.path.join(tmp_path, "tx.json"),
    }
    config_stub.PLAID_CLIENT_NAME = "client"
    config_stub.plaid_client = types.SimpleNamespace()
    sys.modules["app.config"] = config_stub

    log_setup_stub = types.ModuleType("app.config.log_setup")

    class DummyLogger:
        def debug(self, *a, **k):
            pass

        def info(self, *a, **k):
            pass

        def warning(self, *a, **k):
            pass

        def error(self, *a, **k):
            pass

    log_setup_stub.setup_logger = lambda: DummyLogger()
    sys.modules["app.config.log_setup"] = log_setup_stub

    sys.modules["app.extensions"] = types.ModuleType("app.extensions")
    sys.modules["app.extensions"].db = types.SimpleNamespace()
    sys.modules["app.models"] = types.ModuleType("app.models")
    sys.modules["app.models"].Category = type("Category", (), {})
    forecast_stub = types.ModuleType("app.sql.forecast_logic")
    forecast_stub.update_account_history = lambda *a, **k: None
    sys.modules["app.sql.forecast_logic"] = forecast_stub

    # Stub plaid model classes
    model_pkg = types.ModuleType("plaid.model")
    sys.modules["plaid"] = types.ModuleType("plaid")
    sys.modules["plaid.model"] = model_pkg
    class_map = {
        "accounts_get_request": "AccountsGetRequest",
        "country_code": "CountryCode",
        "institutions_get_by_id_request": "InstitutionsGetByIdRequest",
        "investments_holdings_get_request": "InvestmentsHoldingsGetRequest",
        "item_get_request": "ItemGetRequest",
        "item_public_token_exchange_request": "ItemPublicTokenExchangeRequest",
        "link_token_create_request": "LinkTokenCreateRequest",
        "link_token_create_request_user": "LinkTokenCreateRequestUser",
        "products": "Products",
        "transactions_get_request": "TransactionsGetRequest",
        "transactions_get_request_options": "TransactionsGetRequestOptions",
    }
    for mod_name, class_name in class_map.items():
        mod = types.ModuleType(f"plaid.model.{mod_name}")
        setattr(mod, class_name, type(class_name, (), {}))
        setattr(model_pkg, mod_name, mod)
        sys.modules[f"plaid.model.{mod_name}"] = mod

    module_path = os.path.join(
        os.path.dirname(__file__), "..", "backend", "app", "helpers", "plaid_helpers.py"
    )
    spec = importlib.util.spec_from_file_location("plaid_helpers", module_path)
    plaid_helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plaid_helpers)  # type: ignore[attr-defined]
    return plaid_helpers, token_path


@pytest.fixture(autouse=True)
def restore_extensions():
    original = sys.modules.get("app.extensions")
    yield
    if original is not None:
        sys.modules["app.extensions"] = original
    else:
        sys.modules.pop("app.extensions", None)


def test_load_tokens_returns_empty_when_missing(tmp_path):
    plaid_helpers, _ = load_plaid_helpers(tmp_path)
    assert plaid_helpers.load_plaid_tokens() == []


def test_save_and_load_tokens(tmp_path):
    plaid_helpers, path = load_plaid_helpers(tmp_path)
    data = [
        {"user_id": "u1", "access_token": "tok1"},
        {"user_id": "u2", "access_token": "tok2"},
    ]
    plaid_helpers.save_plaid_tokens(data)
    with open(path) as fh:
        assert json.load(fh) == data
    assert plaid_helpers.load_plaid_tokens() == data
