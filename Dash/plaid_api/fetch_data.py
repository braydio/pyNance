import os
from plaid import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = Client(
    client_id=os.getenv('PLAID_CLIENT_ID'),
    secret=os.getenv('PLAID_SECRET'),
    environment=os.getenv('PLAID_ENV')
)

def get_accounts(access_token):
    response = client.Accounts.get(access_token)
    return response['accounts']

def get_transactions(access_token, start_date, end_date):
    response = client.Transactions.get(access_token, start_date, end_date)
    return response['transactions']

if __name__ == "__main__":
    access_token = "access-production-faadecfe-f899-427c-93f7-f39aaee2a636"
    accounts = get_accounts(access_token)
    transactions = get_transactions(access_token, "2023-12-01", "2023-12-27")
    print(f"Accounts: {accounts}")
    print(f"Transactions: {transactions}")
