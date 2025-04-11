
from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration
from app.models import Category
import logging

import requests
from flask import Blueprint, jsonify, request
from app.extensions import db
from app.config import (
    PLAID_BASE_URL,
    PLAID_CLIENT_ID,
    PLAID_CLIENT_NAME,
    PLAID_SECRET,
    logger,
)
logger = logging.getLogger(__name__)

get_categories = Blueprint("/get_categories", __name__)

def generate_link_token(user_id, products=["transactions"]):
    """
    Generate a Plaid link token for the given user and products.
    """
    logger.debug(
        f"Generating link token for plaid with ID: {PLAID_CLIENT_ID} and SECRET: {PLAID_SECRET}"
    )
    logger.debug(f"Using prooducts: {products}")
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "client_name": PLAID_CLIENT_NAME,
        "products": products,
        "country_codes": ["US"],
        "language": "en",
        "user": {"client_user_id": user_id},
    }
    url = f"{PLAID_BASE_URL}/link/token/create"
    logger.debug(f"Generating Plaid link token with payload: {payload}")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("link_token")


def exchange_public_token(public_token):
    """
    Exchange a Plaid public token for an access token and item_id.
    Returns the full exchange response.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token,
    }
    url = f"{PLAID_BASE_URL}/item/public_token/exchange"
    logger.debug("Exchanging Plaid public token for access token")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_accounts(access_token):
    """
    Retrieve accounts data from Plaid.
    """
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    url = f"{PLAID_BASE_URL}/accounts/get"
    logger.debug("Fetching Plaid accounts")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

get_categories.route("/load_categories", methods=["POST"])
def refresh_plaid_categories():
    """
    Fetch all Plaid categories from the Plaid API using the Plaid SDK 
    and populate the categories table via Category.query.
    """

    # First, check how many Category records are in the DB
    try:
        existing_count = Category.query.count()
        if existing_count > 0:
            logger.info(f"{existing_count} categories already exist. Skipping population.")
            return
    except Exception as e:
        logger.error(f"Error checking existing categories: {e}")
        return

    # Prepare Plaid API client
    configuration = Configuration(
        host=PLAID_BASE_URL,
        api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
    )
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    # Fetch categories from Plaid
    try:
        response = client.categories_get({})
        categories_list = response["categories"]
        logger.info(f"Fetched {len(categories_list)} categories from Plaid.")
    except Exception as e:
        logger.erro(f"Error fetching categories from Plaid: {e}")
        return

    try:
        # Ensure we have an "Unknown" category
        unknown_category = Category.query.filter_by(display_name="Unknown").first()
        if not unknown_category:
            unknown_category = Category(display_name="Unknown")
            db.session.add(unknown_category)
            db.session.commit()

        # Populate or update primary/secondary categories
        for cat in categories_list:
            hierarchy = cat.get("hierarchy", [])
            if hierarchy:
                primary_name = hierarchy[0]
                secondary_name = hierarchy[1] if len(hierarchy) > 1 else None
            else:
                # If hierarchy is missing or empty, default to "Unknown"
                primary_name = "Unknown"
                secondary_name = None

            # Look up or create the primary category
            primary_cat = Category.query.filter_by(display_name=primary_name).first()
            if not primary_cat:
                primary_cat = Category(display_name=primary_name)
                db.session.add(primary_cat)
                db.session.commit()
                logger.info(f"Created primary category: {primary_name}")
            else:
                logger.debug(f"Using existing primary category: {primary_name}")

            # Look up or create the secondary category
            if secondary_name and secondary_name != primary_name:
                secondary_cat = Category.query.filter_by(disply_name=secondary_name).first()
                if not secondary_cat:
                    secondary_cat = Category(display_name=secondary_name, parent_id=primary_cat.id)
                    db.session.add(secondary_cat)
                    db.session.commit()
                    logger.info(f"Created secondary category: {secondary_name} under {primary_name}")
                else:
                    if secondary_cat.parent_id != primary_cat.id:
                        secondary_cat.parent_id = primary_cat.id
                        db.session.commit()
                        logger.info(f"Updated secondary category: {secondary_name} under {primary_name}")
                    else:
                        logger.debug(f"Using existing secondary category: {secondary_name}")

        logger.info("Plaid categories successfully populated into the database.")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error populating categories: {e}")


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
