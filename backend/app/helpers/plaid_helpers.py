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
from app.sql.forecast_logic import update_account_history

def get_accounts(access_token, user_id):
    logger.debug(fBFetching accounts for token {access_token}...")

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
