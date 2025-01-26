import os

from config import PLAID_CLIENT_ID, PLAID_ENV, PLAID_SECRET, logger
from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products


def generate_link_token(products_list):
    logger.debug(f"Current Working Dir: {os.getcwd()}")

    # Configure Plaid API client
    configuration = Configuration(
        host=f"https://{PLAID_ENV}.plaid.com",
        api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
    )
    logger.debug(f"Configuration: {configuration}")

    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    logger.debug("Plaid API client configured")

    # Convert product strings to Products() objects
    products = [Products(product) for product in products_list]
    logger.debug(f"Products: {products}")

    # Build request
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="user-unique-id"),
        client_name="My Finance Dashboard",
        products=products,
        country_codes=[CountryCode("US")],
        language="en",
        webhook="https://sample-web-hook.com",
        redirect_uri="https://localhost/callback",
    )
    logger.debug(f"LinkTokenCreateRequest: {request}")

    # Create link token
    try:
        response = client.link_token_create(request)
        link_token = response["link_token"]
        logger.info(f"Link token created: {link_token}")
        return link_token
    except Exception as e:
        logger.error(f"Error creating link token: {e}")
        return None
