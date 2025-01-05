import os
import argparse
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

# Load .env variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
PLAID_ENV = os.getenv("PLAID_ENV")

def generate_link_token(products_list):
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

if __name__ == "__main__":
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description='Generate a Plaid Link Token')
    parser.add_argument(
        '--products', nargs='+', help='List of products (e.g., transactions balance enrich)', required=True)
    args = parser.parse_args()

    # Generate link token with specified products
    generate_link_token(args.products)

