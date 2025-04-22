# plaid_helpers.py
from app.config import (
    plaid_client,
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    PLAID_CLIENT_NAME,
)
import requests
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest

from app.models import Category
from app.extensions import db
from flask import Blueprint, jsonify, request
from app.config.log_setup import setup_logger

logger = setup_logger()

categories = Blueprint("categories", __name__)


def get_item(access_token):
    request = ItemGetRequest(access_token=access_token)
    response = plaid_client.item_get(request)
    return response["item"]


def generate_link_token(user_id, products=["transactions"]):
    logger.debug(f"Generating link token with user_id={user_id}, products={products}")

    try:
        product_enums = [Products(p) for p in products]  # ✅ Enum via string
        country_enum = [CountryCode("US")]  # ✅ Also via string

        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name=PLAID_CLIENT_NAME,
            products=product_enums,
            language="en",
            country_codes=country_enum,
        )

        response = plaid_client.link_token_create(request)
        return response["link_token"]

    except Exception as e:
        logger.error(f"Error generating link token: {e}", exc_info=True)
        raise


def exchange_public_token(public_token):
    logger.debug(f"Exchanging public token: {public_token}")

    try:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = plaid_client.item_public_token_exchange(request)

        access_token = response["access_token"]
        item_id = response["item_id"]

        logger.info(f"Successfully exchanged token. Item ID: {item_id}")
        return {"access_token": access_token, "item_id": item_id}

    except Exception as e:
        logger.error(f"Error exchanging public token: {e}", exc_info=True)
        raise


def get_accounts(access_token):
    logger.debug(f"Fetching accounts for access_token: {access_token[:4]}...")

    try:
        request = AccountsGetRequest(access_token=access_token)
        response = plaid_client.accounts_get(request)
        accounts = response["accounts"]

        logger.info(f"Retrieved {len(accounts)} account(s) from Plaid.")
        return accounts

    except Exception as e:
        logger.error(f"Error fetching accounts: {e}", exc_info=True)
        raise


def get_institution_name(institution_id):
    try:
        request = InstitutionsGetByIdRequest(
            institution_id=institution_id, country_codes=[CountryCode("US")]
        )
        response = plaid_client.institutions_get_by_id(request)
        return response["institution"]["name"]
    except Exception as e:
        logger.warning(f"Failed to fetch institution name for {institution_id}: {e}")
        return institution_id  # fallback


def refresh_plaid_categories():
    url = "https://sandbox.plaid.com/categories/get"  # or use f"https://{PLAID_ENV}.plaid.com/..."
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        count = upsert_categories_from_plaid_data(data)
        logger.info(f"✅ Refreshed {count} Plaid categories.")
    except Exception as e:
        logger.error(f"❌ Failed to refresh Plaid categories: {e}", exc_info=True)


def get_transactions(access_token, start_date, end_date):
    try:
        request = TransactionsGetRequest(
            access_token=access_token, start_date=start_date, end_date=end_date
        )
        response = plaid_client.transactions_get(request)
        return response.to_dict()
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        raise


def get_investments(access_token):
    try:
        request = InvestmentsHoldingsGetRequest(access_token=access_token)
        response = plaid_client.investments_holdings_get(request)
        return response.to_dict()
    except Exception as e:
        logger.error(f"Error fetching investments: {e}", exc_info=True)
        raise
