import os
from functools import partial
from typing import Callable
import plaid
# from plaid.model.configuration import Configuration
# from plaid.model.plaid_environments import PlaidEnvironments
from db.queries import create_plaid_api_event, retrieve_item_by_plaid_access_token
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_ENV = os.getenv("PLAID_ENV", "production")
PLAID_SECRET = os.getenv("PLAID_SECRET_PRODUCTION")

# Validate required environment variables
def validate_env():
    missing_vars = []
    if not PLAID_CLIENT_ID:
        missing_vars.append("PLAID_CLIENT_ID")
    if not PLAID_SECRET:
        missing_vars.append("PLAID_SECRET")
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

validate_env()

# Logging functions
async def default_logger(client_method: str, client_method_args: list, response: dict):
    access_token = client_method_args[0].get("access_token")
    item = await retrieve_item_by_plaid_access_token(access_token)
    await create_plaid_api_event(
        item_id=item["id"],
        user_id=item["user_id"],
        client_method=client_method,
        client_method_args=client_method_args,
        response=response,
    )

async def no_access_token_logger(client_method: str, client_method_args: list, response: dict):
    await create_plaid_api_event(
        item_id=None,
        user_id=None,
        client_method=client_method,
        client_method_args=client_method_args,
        response=response,
    )

# Mapping Plaid client methods to their appropriate logging functions
client_method_logging_fns = {
    "accounts_get": default_logger,
    "institutions_get": no_access_token_logger,
    "institutions_get_by_id": no_access_token_logger,
    "item_public_token_exchange": no_access_token_logger,
    "item_remove": default_logger,
    "link_token_create": no_access_token_logger,
    "transactions_sync": default_logger,
}

# New methods and loggers added for user endpoints
async def user_logger(client_method: str, client_method_args: list, response: dict):
    await create_plaid_api_event(
        item_id=None,
        user_id=None,
        client_method=client_method,
        client_method_args=client_method_args,
        response=response,
    )

# Adding user endpoints to logging functions
client_method_logging_fns.update({
    "user_create": user_logger,
    "user_get": user_logger,
    "user_update": user_logger,
})

class PlaidClientWrapper:
    def __init__(self):
        # Initialize the Plaid client
        configuration = Configuration(
            host=PlaidEnvironments[PLAID_ENV],
            headers={
                "PLAID-CLIENT-ID": PLAID_CLIENT_ID,
                "PLAID-SECRET": PLAID_SECRET,
                "Plaid-Version": "2020-09-14",
            },
        )
        self.client = PlaidApi(configuration)

        # Wrap Plaid client methods with logging
        for method, log_fn in client_method_logging_fns.items():
            setattr(self, method, self.create_wrapped_client_method(method, log_fn))

    def create_wrapped_client_method(self, client_method: str, log_fn: Callable):
        async def wrapped_client_method(*args, **kwargs):
            try:
                response = await getattr(self.client, client_method)(*args, **kwargs)
                await log_fn(client_method, args, response)
                return response
            except Exception as err:
                if hasattr(err, "response") and err.response:
                    await log_fn(client_method, args, err.response.data)
                raise err

        return wrapped_client_method

    async def link_token_create(self, request: dict):
        """
        Simplified method for creating a link token.
        Args:
            request (dict): Payload for link token creation.

        Returns:
            dict: Link token response from Plaid.
        """
        return await self.create_wrapped_client_method("link_token_create", no_access_token_logger)(request)

    async def item_public_token_exchange(self, request: dict):
        """
        Simplified method for exchanging a public token.
        Args:
            request (dict): Payload containing the public token.

        Returns:
            dict: Access token and item ID.
        """
        return await self.create_wrapped_client_method("item_public_token_exchange", no_access_token_logger)(request)

    async def get_item_info(self, access_token: str):
        """
        Fetches metadata for the linked item (institution).

        Args:
            access_token (str): Access token for the linked item.

        Returns:
            tuple: (item_id, institution_name) or (None, None) if an error occurs.
        """
        try:
            response = await self.create_wrapped_client_method("item_get", default_logger)({"access_token": access_token})
            item = response["item"]
            return item.get("item_id"), item.get("institution_name", "Unknown Institution")
        except Exception as e:
            raise ValueError(f"Error fetching item info: {e}")

    async def save_initial_account_data(self, access_token: str, item_id: str):
        """
        Fetches and saves account information for the given access token and item ID.

        Args:
            access_token (str): Access token for the linked item.
            item_id (str): ID of the linked item.
        """
        try:
            response = await self.create_wrapped_client_method("accounts_get", default_logger)({"access_token": access_token})
            accounts = response["accounts"]
            data = {}

            for account in accounts:
                account_id = account["account_id"]
                data[account_id] = {
                    "item_id": item_id,
                    "account_name": account["name"],
                    "type": account["type"],
                    "subtype": account["subtype"],
                    "balances": account.get("balances", {})
                }

            return data
        except Exception as e:
            raise ValueError(f"Error saving account data: {e}")

plaid_client = PlaidClientWrapper()
