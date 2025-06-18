import json

from app.config import (
    FILES,
    PLAID_CLIENT_NAME,
    plaid_client,
)
from app.config.log_setup import setup_logger
from app.extensions import db
from app.models import Category
from app.sql.forecast_logic import update_account_history
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import (
    TransactionsGetRequestOptions,
)

logger = setup_logger()
LAST_TRANSACTIONS = FILES["LAST_TX_REFRESH"]


def save_transactions_json(transactions):
    try:
        with open(LAST_TRANSACTIONS, "w") as f:
            json.dump(transactions, f, indent=4, default=str)
        logger.debug(f"Saved transactions to {LAST_TRANSACTIONS}.")
    except Exception as e:
        logger.error(f"Failed to save transactions: {e}", exc_info=True)


def get_accounts(access_token: str, user_id: str):
    logger.debug(f"Fetching accounts for token {access_token[:4]}...")

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
            logger.debug(f"Passing along user id {user_id} from plaid_helpers")
            account_id = acct.account_id
            balance = acct.balances.available or acct.balances.current
            if account_id and balance is not None:
                update_account_history(
                    account_id=account_id,
                    user_id=user_id,
                    balance=balance,
                )

        logger.info(f"Synced {len(accounts)} Plaid accounts for user {user_id}.")
        return accounts

    except Exception as e:
        logger.error(f"Error syncing accounts: {e}", exc_info=True)
        raise


def get_item(access_token: str):
    try:
        plaid_request = ItemGetRequest(access_token=access_token)
        response = plaid_client.item_get(plaid_request)
        return response.item
    except Exception as e:
        logger.error(f"Error getting item: {e}", exc_info=True)
        raise


def generate_link_token(user_id: str, products=["transactions"]):
    logger.debug(f"Generating link token with user_id={user_id}, products={products}")

    try:
        product_enums = [Products(p) for p in products]
        country_enum = [CountryCode("US")]

        plaid_request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name=PLAID_CLIENT_NAME,
            products=product_enums,
            language="en",
            country_codes=country_enum,
        )

        response = plaid_client.link_token_create(plaid_request)
        return response.link_token

    except Exception as e:
        logger.error(f"Error generating link token: {e}", exc_info=True)
        raise


def exchange_public_token(public_token: str):
    logger.debug(f"Exchanging public token: {public_token}")

    try:
        plaid_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = plaid_client.item_public_token_exchange(plaid_request)

        access_token = response.access_token
        item_id = response.item_id

        logger.info(f"Successfully exchanged token. Item ID: {item_id}")
        return {"access_token": access_token, "item_id": item_id}

    except Exception as e:
        logger.error(f"Error exchanging public token: {e}", exc_info=True)
        raise


def get_institution_name(institution_id: str):
    try:
        plaid_request = InstitutionsGetByIdRequest(
            institution_id=institution_id, country_codes=[CountryCode("US")]
        )
        response = plaid_client.institutions_get_by_id(plaid_request)
        return response.institution.name
    except Exception as e:
        logger.warning(f"Failed to fetch institution name for {institution_id}: {e}")
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
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
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
        logger.error(f"Error fetching investments: {e}", exc_info=True)
        raise
