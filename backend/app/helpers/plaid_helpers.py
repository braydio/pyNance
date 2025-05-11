from app.config import (
    plaid_client,
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    PLAID_CLIENT_NAME,
    FILES,
)
from app.sql.forecast_logic import update_account_history
from app.models import Category
from app.extensions import db
from flask import Blueprint, jsonify, request
from app.config.log_setup import setup_logger
import json
import requests

from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest

logger = setup_logger()
LAST_TRANSACTIONS = FILES["LAST_TX_REFRESH"]

def save_transactions_json(transactions):
    try:
        with open(LAST_TRANSACTIONS, "w") as f:
            json.dump(transactions, f, indent=4, default=str)
        logger.info(f"Saved transactions to {LAST_TRANSACTIONS}.")
    except Exception as e:
        logger.error(f"Failed to save transactions: {e}", exc_info=True)

def get_accounts(access_token, user_id):
    logger.debug(f"Fetching accounts for token {access_token[:4]}...")

    try:
        request = AccountsGetRequest(access_token=access_token)
        response = plaid_client.accounts_get(request)
        accounts = response["accounts"]

        for acct in accounts:
            account_id = acct["account_id"]
            balance = acct["balances"].get("available") or acct["balances"].get("current")
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

def get_item(access_token):
    request = ItemGetRequest(access_token=access_token)
    response = plaid_client.item_get(request)
    return response["item"]

def generate_link_token(user_id, products=["transactions"]):
    logger.debug(f"Generating link token with user_id={user_id}, products={products}")

    try:
        product_enums = [Products(p) for p in products]
        country_enum = [CountryCode("US")]

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
    logger.warning("Plaid /categories/get endpoint is deprecated. Skipping category refresh.")
    return []

def get_transactions(access_token, start_date, end_date):
    try:
        request = TransactionsGetRequest(
            access_token=access_token, start_date=start_date, end_date=end_date
        )
        response = plaid_client.transactions_get(request)
        transactions = [tx.to_dict() for tx in response["transactions"]]

        save_transactions_json(transactions)
        return transactions
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
        db.session.flush()  # get ID

    return category

def get_investments(access_token):
    try:
        request = InvestmentsHoldingsGetRequest(access_token=access_token)
        response = plaid_client.investments_holdings_get(request)
        return response.to_dict()
    except Exception as e:
        logger.error(f"Error fetching investments: {e}", exc_info=True)
        raise

