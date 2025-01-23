import os
import argparse
import json
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from utils.helper_utils import logger

# Load .env variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV")

def generate_link_token(products_list):
    logger.debug(f"Current Working Dir: {os.getcwd()}")
    # Configure Plaid API client
    configuration = Configuration(
        host=f"https://{PLAID_ENV}.plaid.com",
        api_key={
            'clientId': CLIENT_ID,
            'secret': SECRET_KEY
        }
    )
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    # Convert product strings to Products() objects
    products = [Products(product) for product in products_list]

    # Build request
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id='user-unique-id'),
        client_name='My Finance Dashboard',
        products=products,
        country_codes=[CountryCode('US')],
        language='en',
        webhook='https://sample-web-hook.com',
        redirect_uri='https://localhost/callback'
    )

    # Create link token
    try:
        response = client.link_token_create(request)
        link_token = response['link_token']
        print(f"Link token created: {link_token}")
        return link_token
    except Exception as e:
        print(f"Error creating link token: {e}")
        return None

# Utility functions
def ensure_directory_exists(directory_path):
    """
    Ensures that the given directory exists. Creates it if it doesn't.
    
    Args:
        directory_path (str): Path to the directory.
    """
    os.makedirs(directory_path, exist_ok=True)

def ensure_file_exists(file_path, default_content=None):
    """
    Ensures that the given file exists. Creates it if it doesn't, with optional default content.

    Args:
        file_path (str): Path to the file.
        default_content (str, dict, list, optional): Content to write to the file if it's created. Default is None.
    """
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            if default_content is not None:
                if isinstance(default_content, (dict, list)):
                    import json
                    json.dump(default_content, file, indent=2)
                else:
                    file.write(default_content)
            else:
                file.write("")

def save_and_parse_response(response, file_path):
    """
    Save a JSON response to a file and parse it.

    Args:
        response (requests.Response): Response object from an API call.
        file_path (str): Path to save the JSON file.

    Returns:
        dict: Parsed JSON content from the file.
    """
    ensure_directory_exists(os.path.dirname(file_path))
    
    # Save response JSON to file
    with open(file_path, "w") as temp_file:
        json.dump(response.json(), temp_file, indent=2)
    
    # Parse the saved file
    return load_json(file_path)

def load_json(file_path):
    """
    Load JSON content from a file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON content from the file.
    """
    with open(file_path, "r") as temp_file:
        app.run(debug=True, port=5001)

def refresh_accounts_by_access_token(access_token):
    client = ApiClient(client_id='your_client_id', secret='your_secret', environment='sandbox')

    # Refresh linked accounts via Plaid API
    response = client.Transactions.refresh(access_token)

    return response



def refresh_plaid_data(account_group):
    # Plaid client initialization
    client = ApiClient(client_id='your_client_id', secret='your_secret', environment='sandbox')

    # Fetch accounts/items based on the account group
    # (You'll need to map `account_group` to the corresponding Plaid items or accounts)
    item_id = get_item_id_for_group(account_group)  # Replace with actual mapping logic

    # Trigger a data refresh
    response = client.Item.refresh(item_id)

    return response


if __name__ == "__main__":
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description='Generate a Plaid Link Token')
    parser.add_argument(
        '--products', nargs='+', help='List of products (e.g., transactions balance enrich)', required=True)
    args = parser.parse_args()

    # Generate link token with specified products
    generate_link_token(args.products)

