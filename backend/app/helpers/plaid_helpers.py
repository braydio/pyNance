
from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration

from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products

from app.config import plaid_client, PLAID_CLIENT_NAME
from app.models import Category
from app.extensions import db
from flask import Blueprint, jsonify, request
import logging  # ← import logging, not `from app.config import logging`

logger = logging.getLogger(__name__)
get_categories = Blueprint("get_categories", __name__)

def get_item(access_token):
    request = ItemGetRequest(access_token=access_token)
    response = plaid_client.item_get(request)
    return response["item"]

def generate_link_token(user_id, products=["transactions"]):
    logger.debug(f"Generating link token with user_id={user_id}, products={products}")

    try:
        product_enums = [Products(p) for p in products]        # ✅ Enum via string
        country_enum = [CountryCode("US")]                     # ✅ Also via string

        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name=PLAID_CLIENT_NAME,
            products=product_enums,
            language="en",
            country_codes=country_enum
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
        return {
            "access_token": access_token,
            "item_id": item_id
        }

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

get_categories.route("/load_categories", methods=["POST"])
def refresh_plaid_categories():
    """
    Fetch categories from Plaid and insert them into the local Category table
    with hierarchy: primary → detailed
    """
    url =  f"{PLAID_BASE_URL}/categories/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        for cat in data.get("categories", []):
            hierarchy = cat.get("hierarchy", [])
            plaid_cat_id = cat.get("category_id")
            if not plaid_cat_id:
                continue

            # Determine level
            if len(hierarchy) == 1:
                # Primary-level category
                primary_name = hierarchy[0]
                existing = Category.query.filter_by(plaid_category_id=plaid_cat_id).first()
                if not existing:
                    new_primary = Category(
                        plaid_category_id=plaid_cat_id + "_primary",
                        primary_category=primary_name,
                        detailed_category=None,
                        display_name=primary_name,
                        parent_id=None
                    )
                    db.session.add(new_primary)
                    db.session.flush()  # get ID for parent
                else:
                    continue  # already exists

            elif len(hierarchy) >= 2:
                # Subcategory
                primary_name = hierarchy[0]
                detailed_name = hierarchy[1]

                # Find or create parent
                parent = Category.query.filter_by(display_name=primary_name, parent_id=None).first()
                if not parent:
                    parent = Category(
                        plaid_category_id=f"{plaid_cat_id}_primary",
                        primary_category=primary_name,
                        display_name=primary_name
                    )
                    db.session.add(parent)
                    db.session.flush()

                # Now insert child
                existing = Category.query.filter_by(plaid_category_id=plaid_cat_id).first()
                if not existing:
                    new_cat = Category(
                        plaid_category_id=plaid_cat_id,
                        primary_category=primary_name,
                        detailed_category=detailed_name,
                        display_name=detailed_name,
                        parent_id=parent.id
                    )
                    db.session.add(new_cat)

        db.session.commit()
        logger.info("✅ Plaid categories refreshed successfully.")

    except Exception as e:
        logger.error(f"❌ Failed to refresh Plaid categories: {e}", exc_info=True)


def get_transactions(access_token, start_date, end_date):
    """
    Retrieve transactions from Plaid for the given date range.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
        "start_date": start_date,
        "end_date": end_date,
    }
    url = f"{PLAID_BASE_URL}/transactions/get"
    logger.debug("Fetching Plaid transactions")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_investments(access_token):
    """
    Retrieve investments holdings from Plaid.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    url = f"{PLAID_BASE_URL}/investments/holdings/get"
    logger.debug("Fetching Plaid investments holdings")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()
