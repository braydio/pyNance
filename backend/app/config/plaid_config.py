"""Initialize the Plaid API client if dependencies are available.

This module configures and exposes a :data:`plaid_client` instance used by the
rest of the application. Tests and environments without Plaid credentials or
packages should still be able to import this module, so the client defaults to
``None`` when requirements are missing.
"""

from __future__ import annotations

# pylint: disable=import-error,invalid-name,broad-exception-caught

# Provide safe defaults to allow imports when Plaid dependencies are absent.
PLAID_BASE_URL = "https://sandbox.plaid.com"
plaid_client = None

try:  # pragma: no cover - exercised indirectly
    from plaid.api import plaid_api
    from plaid.api_client import ApiClient
    from plaid.configuration import Configuration

    from .environment import PLAID_CLIENT_ID, PLAID_ENV, PLAID_SECRET

    PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"
    configuration = Configuration(
        host=PLAID_BASE_URL,
        api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
    )
    api_client = ApiClient(configuration)
    plaid_client = plaid_api.PlaidApi(api_client)
except Exception:  # noqa: BLE001
    # If Plaid isn't configured, expose a ``None`` client to allow tests to run.
    plaid_client = None
