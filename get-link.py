from plaid.api import plaid_api
from plaid.model import LinkTokenCreateRequest, Products, CountryCode, TransactionsGetRequest, AccountsGetRequest
import os

# Initialize the Plaid client
client = plaid_api.PlaidApi.from_env()

# 1. Generate a link token
def create_link_token():
    try:
        request = LinkTokenCreateRequest(
            user={"client_user_id": "unique-user-id"},
            client_name="My Finance App",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en",
        )
        response = client.link_token_create(request)
        return response["link_token"]
    except Exception as e:
        print(f"Error creating link token: {e}")
        return None

# 2. Exchange public token for access token
def exchange_public_token(public_token):
    try:
        response = client.item_public_token_exchange({"public_token": public_token})
        return response["access_token"]
    except Exception as e:
        print(f"Error exchanging public token: {e}")
        return None

# 3. Fetch transactions
def get_transactions(access_token):
    try:
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date="2023-01-01",
            end_date="2023-12-31",
        )
        response = client.transactions_get(request)
        return response["transactions"]
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return []

# 4. Fetch accounts
def get_account_details(access_token):
    try:
        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        return response["accounts"]
    except Exception as e:
        print(f"Error fetching account details: {e}")
        return []

# Workflow
if __name__ == "__main__":
    # Step 1: Create a link token and print it
    link_token = create_link_token()
    print(f"Link Token: {link_token}")
    
    # Step 2: Simulate public token received from frontend
    public_token = "sandbox-public-token"  # Replace with actual token from frontend
    access_token = exchange_public_token(public_token)
    print(f"Access Token: {access_token}")
    
    # Step 3: Fetch transactions
    if access_token:
        transactions = get_transactions(access_token)
        print("Transactions:", transactions)
        
        accounts = get_account_details(access_token)
        print("Accounts:", accounts)
