
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
