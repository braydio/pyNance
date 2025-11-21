"""Helper utilities for interacting with the Plaid API.

Logging is routed through the module logger and avoids emitting sensitive token
material. Messages are reserved for notable lifecycle events and failures to
keep logs concise.
"""

import json
import logging

from app.config import BACKEND_PUBLIC_URL, FILES, PLAID_CLIENT_NAME, plaid_client
from app.extensions import db
from app.models import Category
from app.sql.forecast_logic import update_account_history
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.investments_transactions_get_request import (
    InvestmentsTransactionsGetRequest,
)
from plaid.model.investments_transactions_get_request_options import (
    InvestmentsTransactionsGetRequestOptions,
)
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

logger = logging.getLogger(__name__)
LAST_TRANSACTIONS = FILES["LAST_TX_REFRESH"]
PLAID_TOKENS = FILES["PLAID_TOKENS"]


def load_plaid_tokens():
    """Load Plaid tokens from the designated JSON file."""
    try:
        logger.info("Loading Plaid tokens from %s", PLAID_TOKENS)
        with open(PLAID_TOKENS, "r") as f:
            tokens = json.load(f)
        logger.info("Loaded %d Plaid token(s) from %s", len(tokens), PLAID_TOKENS)
        return tokens
    except FileNotFoundError:
        logger.warning(
            "Tokens file not found at %s, returning empty list.",
            PLAID_TOKENS,
        )
        return []
    except json.JSONDecodeError as e:
        logger.error(
            "Error decoding tokens file at %s: %s",
            PLAID_TOKENS,
            e,
            exc_info=True,
        )
        return []


def save_plaid_tokens(tokens):
    """Save Plaid tokens to the designated JSON file."""
    try:
        logger.info("Saving %d Plaid token(s) to %s", len(tokens), PLAID_TOKENS)
        with open(PLAID_TOKENS, "w") as f:
            json.dump(tokens, f, indent=4)
        logger.info("Plaid tokens saved successfully to %s", PLAID_TOKENS)
    except Exception as e:
        logger.error(
            "Error saving tokens to %s: %s",
            PLAID_TOKENS,
            e,
            exc_info=True,
        )


def save_transactions_json(transactions):
    try:
        with open(LAST_TRANSACTIONS, "w") as f:
            json.dump(transactions, f, indent=4, default=str)
        try:
            total = len(transactions)
        except TypeError:
            total = None
        if total is not None:
            logger.info(
                "Saved %d transaction(s) to %s.",
                total,
                LAST_TRANSACTIONS,
            )
        else:
            logger.info("Saved transactions to %s.", LAST_TRANSACTIONS)
    except Exception as e:
        logger.error("Failed to save transactions: %s", e, exc_info=True)


def get_accounts(access_token: str, user_id: str):
    logger.info("Fetching Plaid accounts for user %s", user_id or "<missing>")

    if not user_id:
        logger.error("Missing user_id in get_accounts() — aborting.")
        raise ValueError("user_id must be provided to get_accounts")

    try:
        plaid_request = AccountsGetRequest(access_token=access_token)
        response = plaid_client.accounts_get(plaid_request)
        accounts = response.accounts

        for acct in accounts:
            if not user_id:
                logger.warning(
                    "[WARN] Missing user_id while syncing account_id=%s", acct
                )
            account_id = acct.account_id
            balance = acct.balances.available or acct.balances.current
            if account_id and balance is not None:
                update_account_history(
                    account_id=account_id,
                    user_id=user_id,
                    balance=balance,
                )

        logger.info(
            "Synced %d Plaid accounts for user %s.",
            len(accounts),
            user_id,
        )
        return accounts

    except Exception as e:
        logger.error("Error syncing accounts: %s", e, exc_info=True)
        raise


def get_item(access_token: str):
    try:
        plaid_request = ItemGetRequest(access_token=access_token)
        response = plaid_client.item_get(plaid_request)
        return response.item
    except Exception as e:
        logger.error("Error getting item: %s", e, exc_info=True)
        raise


def generate_link_token(user_id: str, products=None):
    if products is None:
        products = ["transactions"]
    logger.info("Generating link token for user %s", user_id)

    try:
        product_enums = [Products(p) for p in products]
        country_enum = [CountryCode("US")]

        webhook_url = None
        if BACKEND_PUBLIC_URL:
            # Ensure no trailing slash
            base = str(BACKEND_PUBLIC_URL).rstrip("/")
            webhook_url = f"{base}/api/webhooks/plaid"

        plaid_request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name=PLAID_CLIENT_NAME,
            products=product_enums,
            language="en",
            country_codes=country_enum,
            webhook=webhook_url,
        )

        response = plaid_client.link_token_create(plaid_request)
        return response.link_token

    except Exception as e:
        logger.error("Error generating link token: %s", e, exc_info=True)
        raise


def exchange_public_token(public_token: str):
    logger.info("Exchanging public token for access token")

    try:
        plaid_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = plaid_client.item_public_token_exchange(plaid_request)

        access_token = response.access_token
        item_id = response.item_id

        logger.info("Successfully exchanged token. Item ID: %s", item_id)
        return {"access_token": access_token, "item_id": item_id}

    except Exception as e:
        logger.error("Error exchanging public token: %s", e, exc_info=True)
        raise


def remove_item(access_token: str) -> None:
    """Remove a Plaid item associated with ``access_token``."""
    try:
        plaid_request = ItemRemoveRequest(access_token=access_token)
        plaid_client.item_remove(plaid_request)
    except Exception as e:
        logger.error("Error removing Plaid item: %s", e, exc_info=True)
        raise


def get_institution_name(institution_id: str):
    try:
        plaid_request = InstitutionsGetByIdRequest(
            institution_id=institution_id, country_codes=[CountryCode("US")]
        )
        response = plaid_client.institutions_get_by_id(plaid_request)
        return response.institution.name
    except Exception as e:
        logger.warning(
            "Failed to fetch institution name for %s: %s",
            institution_id,
            e,
        )
        return institution_id  # fallback


def refresh_plaid_categories():
    logger.warning(
        "Plaid /categories/get endpoint is deprecated. Skipping category refresh."
    )
    return []


def get_transactions(access_token: str, start_date: str, end_date: str):
    """Return all transactions between ``start_date`` and ``end_date``.

    The Plaid ``/transactions/get`` endpoint returns a maximum of 500
    transactions per request. This helper automatically paginates the
    results by incrementing the ``offset`` parameter until all
    ``total_transactions`` are retrieved.
    """

    try:
        all_transactions = []
        offset = 0
        count = 500

        while True:
            options = TransactionsGetRequestOptions(count=count, offset=offset)
            plaid_request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=options,
            )
            response = plaid_client.transactions_get(plaid_request)

            batch = [tx.to_dict() for tx in response.transactions]
            all_transactions.extend(batch)

            if len(all_transactions) >= response.total_transactions:
                break

            offset += len(batch)

        save_transactions_json(all_transactions)
        return all_transactions
    except Exception as e:
        logger.error("Error fetching transactions: %s", e, exc_info=True)
        raise


def resolve_or_create_category(category_path):
    primary = category_path[0] if len(category_path) > 0 else "Uncategorized"
    secondary = category_path[1] if len(category_path) > 1 else None

    category = Category.query.filter_by(
        primary_category=primary, detailed_category=secondary
    ).first()

    if not category:
        category = Category(
            primary_category=primary,
            detailed_category=secondary,
            display_name=f"{primary} > {secondary}" if secondary else primary,
            plaid_category_id=None,
        )
        db.session.add(category)
        db.session.flush()  # assumes external commit follows

    return category


def get_investments(access_token: str):
    try:
        plaid_request = InvestmentsHoldingsGetRequest(access_token=access_token)
        response = plaid_client.investments_holdings_get(plaid_request)
        return response.to_dict()
    except Exception as e:
        logger.error("Error fetching investments: %s", e, exc_info=True)
        raise


def get_investment_transactions(access_token: str, start_date, end_date):
    """Return investment transactions between start_date and end_date.

    Accepts ``start_date``/``end_date`` as ``datetime.date``, ``datetime.datetime``,
    or ISO ``YYYY-MM-DD`` strings and coerces them to dates required by Plaid's
    typed request model.

    Paginates using options.count/options.offset similar to transactions.
    """
    from datetime import date, datetime

    def _coerce_to_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            # Try strict format first, then ISO
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return date.fromisoformat(value)
        return datetime.utcnow().date()

    try:
        start_dt = _coerce_to_date(start_date)
        end_dt = _coerce_to_date(end_date)

        all_txs = []
        offset = 0
        count = 500
        while True:
            options = InvestmentsTransactionsGetRequestOptions(
                count=count, offset=offset
            )
            req = InvestmentsTransactionsGetRequest(
                access_token=access_token,
                start_date=start_dt,
                end_date=end_dt,
                options=options,
            )
            resp = plaid_client.investments_transactions_get(req)
            batch = [t.to_dict() for t in resp.investment_transactions]
            all_txs.extend(batch)
            # Plaid returns .total_investment_transactions
            total = getattr(resp, "total_investment_transactions", None)
            if total is None or len(all_txs) >= total or len(batch) == 0:
                break
            offset += len(batch)
        return all_txs
    except Exception as e:
        logger.error("Error fetching investment transactions: %s", e, exc_info=True)
        raise
