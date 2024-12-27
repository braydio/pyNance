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

def exchange_public_token(public_token):
    response = client.Item.public_token.exchange(public_token)
    return response['access_token'], response['item_id']

if __name__ == "__main__":
    public_token = "public-token"
    access_token, item_id = exchange_public_token(public_token)
    print(f"Access Token: {access_token}")
    print(f"Item ID: {item_id}")
