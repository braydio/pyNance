#!/usr/bin/env python3
"""Link Plaid accounts from stored access tokens.

Usage:
    python scripts/plaid_link_from_token.py [token_file]

The token file defaults to ``backend/data/PlaidTokens.json`` as defined by
``FILES["PLAID_TOKENS"]``. It should contain a list of objects with ``user_id``
and ``access_token`` keys. For each token the script fetches account metadata
from Plaid, inserts or updates the associated ``Account`` rows and ensures a
``PlaidAccount`` entry exists.
"""
# mypy: ignore-errors
# pylint: disable=import-error

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Dict, List

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Stub minimal app package and db extension
app_pkg = types.ModuleType("app")
extensions_mod = types.ModuleType("app.extensions")
db = SQLAlchemy()
extensions_mod.db = db
app_pkg.extensions = extensions_mod
app_pkg.__path__ = []
sys.modules["app"] = app_pkg
sys.modules["app.extensions"] = extensions_mod

# Load configuration
config_path = BACKEND_DIR / "app" / "config" / "__init__.py"
config_spec = importlib.util.spec_from_file_location("app.config", config_path)
config_mod = importlib.util.module_from_spec(config_spec)  # type: ignore[arg-type]
config_spec.loader.exec_module(config_mod)  # type: ignore[arg-type]
sys.modules["app.config"] = config_mod
FILES = config_mod.FILES
logger = config_mod.logger
DATABASE_URI = config_mod.SQLALCHEMY_DATABASE_URI

# Load forecast_logic for plaid_helpers dependency
forecast_path = BACKEND_DIR / "app" / "sql" / "forecast_logic.py"
forecast_spec = importlib.util.spec_from_file_location(
    "app.sql.forecast_logic", forecast_path
)
forecast_mod = importlib.util.module_from_spec(forecast_spec)  # type: ignore[arg-type]
forecast_spec.loader.exec_module(forecast_mod)  # type: ignore[arg-type]
sys.modules["app.sql.forecast_logic"] = forecast_mod

# Load models
models_path = BACKEND_DIR / "app" / "models.py"
models_spec = importlib.util.spec_from_file_location("app.models", models_path)
models_mod = importlib.util.module_from_spec(models_spec)  # type: ignore[arg-type]
models_spec.loader.exec_module(models_mod)  # type: ignore[arg-type]
sys.modules["app.models"] = models_mod
Account = models_mod.Account
PlaidAccount = models_mod.PlaidAccount

# Load helpers
plaid_helpers_path = BACKEND_DIR / "app" / "helpers" / "plaid_helpers.py"
plaid_spec = importlib.util.spec_from_file_location(
    "app.helpers.plaid_helpers", plaid_helpers_path
)
plaid_mod = importlib.util.module_from_spec(plaid_spec)  # type: ignore[arg-type]
plaid_spec.loader.exec_module(plaid_mod)  # type: ignore[arg-type]
sys.modules["app.helpers.plaid_helpers"] = plaid_mod
get_accounts = plaid_mod.get_accounts
get_item = plaid_mod.get_item
get_institution_name = plaid_mod.get_institution_name

# Load account_logic
account_logic_path = BACKEND_DIR / "app" / "sql" / "account_logic.py"
account_spec = importlib.util.spec_from_file_location(
    "app.sql.account_logic", account_logic_path
)
account_mod = importlib.util.module_from_spec(account_spec)  # type: ignore[arg-type]
account_spec.loader.exec_module(account_mod)  # type: ignore[arg-type]
sys.modules["app.sql.account_logic"] = account_mod


def create_app(db_uri: str) -> Flask:
    """Return a minimal Flask application bound to ``db_uri``."""

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def load_tokens(path: Path) -> List[Dict[str, str]]:
    """Read token data from ``path`` if it exists."""

    if not path.exists():
        logger.error("Token file not found: %s", path)
        return []
    try:
        with path.open() as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse token file: %s", exc)
        return []
    if not isinstance(data, list):
        logger.error("Token file must contain a list of objects")
        return []
    return data


def sync_from_token(user_id: str, access_token: str) -> int:
    """Sync accounts for a single token and ensure PlaidAccount rows."""

    item = get_item(access_token)
    item_id = item.get("item_id")
    institution_id = item.get("institution_id")
    institution_name = get_institution_name(institution_id)

    accounts = get_accounts(access_token, user_id)
    for acct in accounts:
        acct["institution_name"] = institution_name
    account_mod.upsert_accounts(
        user_id, accounts, provider="Plaid", access_token=access_token
    )

    inserted = 0
    for acct in accounts:
        acct_id = acct.get("account_id")
        if not acct_id:
            continue
        exists = PlaidAccount.query.filter_by(account_id=acct_id).first()
        if exists:
            continue
        new_plaid = PlaidAccount(
            account_id=acct_id,
            access_token=access_token,
            item_id=item_id,
            institution_id=institution_id,
        )
        db.session.add(new_plaid)
        inserted += 1
    db.session.commit()
    return inserted


def main() -> None:
    """Process the token file and sync accounts."""
    token_file = Path(sys.argv[1]) if len(sys.argv) > 1 else FILES["PLAID_TOKENS"]
    app = create_app(DATABASE_URI)
    total = 0
    with app.app_context():
        tokens = load_tokens(token_file)
        for entry in tokens:
            user_id = entry.get("user_id")
            access_token = entry.get("access_token")
            if not user_id or not access_token:
                logger.warning("Skipping invalid token entry: %s", entry)
                continue
            total += sync_from_token(user_id, access_token)
    logger.info("Inserted or updated %s accounts", total)


if __name__ == "__main__":
    main()
