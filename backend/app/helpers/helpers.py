import json
import os
from pathlib import Path

import requests
from app.config import (
    FILES,
    PLAID_BASE_URL,
    PLAID_CLIENT_ID,
    PLAID_ENV,
    PLAID_SECRET,
    logger,
)
from app.extensions import Session


# -------------------------
# Plaid API Helpers
# -------------------------
def exchange_public_token(public_token: str):
    """
    Exchange a public token for an access token.
    """
    url = f"https://{PLAID_ENV}.plaid.com/item/public_token/exchange"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "public_token": public_token,
    }
    masked_payload = payload.copy()
    masked_payload["client_id"] = "****"
    masked_payload["secret"] = "****"
    logger.debug(f"Exchanging public token at {url} with payload: {masked_payload}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.debug(f"Response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            exchange_data = response.json()
            access_token = exchange_data.get("access_token")
            logger.info(f"Access token generated: {access_token}")
            return {
                "access_token": access_token,
                "item_id": exchange_data.get("item_id"),
            }
        else:
            logger.error(f"Error exchanging token: {response.json()}")
            return None
    except requests.RequestException as re:
        logger.error(f"Request exception during token exchange: {re}")
        return None


def save_and_parse_response(response: requests.Response, file_path: str):
    """
    Save the API response to disk and then load it.
    """
    ensure_directory_exists(os.path.dirname(file_path))
    with open(file_path, "w") as f:
        json.dump(response.json(), f, indent=2)
    resolved_path = Path(file_path).resolve()
    logger.debug(f"Saved response to {resolved_path}")
    return load_json(file_path)


def get_item_info(access_token: str):
    """
    Retrieve item metadata using the /item/get endpoint.
    """
    url = f"https://{PLAID_BASE_URL}/item/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        item_data = response.json()
        institution_name = item_data["item"].get(
            "institution_name", "Unknown Institution"
        )
        item_id = item_data["item"].get("item_id")

        # Update local file with item metadata
        ensure_file_exists(FILES["LINKED_ITEMS"], default_content={})
        try:
            existing_data = load_json(FILES["LINKED_ITEMS"])
        except Exception:
            existing_data = {}

        existing_data[item_id] = {
            "institution_name": institution_name,
            "item_id": item_id,
            "products": item_data["item"].get("products", []),
            "status": item_data.get("status", {}),
        }
        save_json_with_backup(FILES["LINKED_ITEMS"], existing_data)
        logger.info(f"Linked to {institution_name} with item ID: {item_id}")
        return item_id, institution_name

    except Exception as e:
        logger.error(f"Error in get_item_info: {e}")
        return None, None


def fetch_and_populate_categories():
    """
    Fetch all Plaid categories from the Plaid API using the Plaid SDK and populate the SQL categories table.
    """
    from plaid.api import plaid_api
    from plaid.api_client import ApiClient
    from plaid.configuration import Configuration

    session = Session()
    try:
        existing_count = session.query(Category).count()
        if existing_count > 0:
            logger.info(
                f"{existing_count} categories already exist. Skipping population."
            )
            return
    except Exception as e:
        logger.error(f"Error checking categories: {e}")
        return
    finally:
        session.close()

    configuration = Configuration(
        host=f"https://{PLAID_ENV}.plaid.com",
        api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
    )
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    try:
        response = client.categories_get({})
        categories_list = response["categories"]
        logger.info(f"Fetched {len(categories_list)} categories from Plaid.")
    except Exception as e:
        logger.error(f"Error fetching categories from Plaid: {e}")
        return

    session = Session()
    try:
        unknown_category = session.query(Category).filter_by(name="Unknown").first()
        if not unknown_category:
            unknown_category = Category(name="Unknown")
            session.add(unknown_category)
            session.commit()

        for cat in categories_list:
            hierarchy = cat.get("hierarchy", [])
            if hierarchy:
                primary_name = hierarchy[0]
                secondary_name = hierarchy[1] if len(hierarchy) > 1 else None
            else:
                primary_name = "Unknown"
                secondary_name = None

            primary_cat = session.query(Category).filter_by(name=primary_name).first()
            if not primary_cat:
                primary_cat = Category(name=primary_name)
                session.add(primary_cat)
                session.commit()
                logger.info(f"Created primary category: {primary_name}")
            else:
                logger.debug(f"Using existing primary category: {primary_name}")

            if secondary_name and secondary_name != primary_name:
                secondary_cat = (
                    session.query(Category).filter_by(name=secondary_name).first()
                )
                if not secondary_cat:
                    secondary_cat = Category(
                        name=secondary_name, parent_id=primary_cat.id
                    )
                    session.add(secondary_cat)
                    session.commit()
                    logger.info(
                        f"Created secondary category: {secondary_name} under {primary_name}"
                    )
                else:
                    if secondary_cat.parent_id != primary_cat.id:
                        secondary_cat.parent_id = primary_cat.id
                        session.commit()
                        logger.info(
                            f"Updated secondary category: {secondary_name} under {primary_name}"
                        )
                    else:
                        logger.debug(
                            f"Using existing secondary category: {secondary_name}"
                        )
        logger.info("Plaid categories successfully populated into the database.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error populating categories: {e}")
    finally:
        session.close()


def get_investments_item_info(access_token: str):
    """
    Retrieve investments item metadata using the /item/get endpoint.
    """
    url = f"https://{PLAID_BASE_URL}/item/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        item_data = response.json()
        institution_name = item_data["item"].get(
            "institution_name", "Unknown Institution"
        )
        item_id = item_data["item"].get("item_id")
        logger.info(f"Retrieved investments item info: {institution_name}, {item_id}")
        return item_id, institution_name
    except Exception as e:
        logger.error(f"Error retrieving investments item info: {e}")
        return None, None


def save_initial_investments_data(access_token: str, item_id: str):
    """
    Save the initial investments holdings data using the /investments/holdings/get endpoint.
    """
    url = f"https://{PLAID_BASE_URL}/investments/holdings/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": access_token,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        investments_data = response.json()
        ensure_file_exists(FILES["LINKED_INVESTMENT_ACCOUNTS"], default_content={})
        try:
            existing_data = load_json(FILES["LINKED_INVESTMENT_ACCOUNTS"])
        except Exception:
            existing_data = {}

        for holding in investments_data.get("holdings", []):
            account_id = holding.get("account_id")
            existing_data[account_id] = {
                "item_id": item_id,
                "holding": holding,
            }
        save_json_with_backup(FILES["LINKED_INVESTMENT_ACCOUNTS"], existing_data)
        logger.info(f"Initial investments data saved for item_id {item_id}.")
    except Exception as e:
        logger.error(f"Error in save_initial_investments_data: {e}")


def generate_link_token(products_list: list, user_id: str = "default_user"):
    """
    Generate a link token for the provided list of Plaid products using the Plaid SDK.
    """
    from plaid.api import plaid_api
    from plaid.api_client import ApiClient
    from plaid.configuration import Configuration
    from plaid.model.country_code import CountryCode
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products

    configuration = Configuration(
        host=f"https://{PLAID_ENV}.plaid.com",
        api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
    )
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    # Use the provided user_id here.
    products = [Products(product) for product in products_list]
    request_payload = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=user_id),
        client_name="My Finance Dashboard",
        products=products,
        country_codes=[CountryCode("US")],
        language="en",
        webhook="https://sample-web-hook.com",  # Replace or remove as needed
        redirect_uri="https://localhost/callback",  # Replace as needed
    )

    try:
        response = client.link_token_create(request_payload)
        link_token = response["link_token"]
        logger.info(f"Link token created: {link_token}")
        return link_token
    except Exception as e:
        logger.error(f"Error creating link token: {e}")
        return None


def get_categories():
    """
    Retrieve Plaid categories.
    """
    url = f"https://{PLAID_ENV}.plaid.com/categories/get"
    headers = {"Content-Type": "application/json"}
    payload = {"client_id": PLAID_CLIENT_ID, "secret": PLAID_SECRET}
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return {"error": str(e)}
