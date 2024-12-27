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

def create_link_token(user_id):
    response = client.LinkToken.create({
        'user': {'client_user_id': user_id},
        'client_name': 'Finance Dash',
        'products': ['transactions'],
        'country_codes': ['US'],
        'language': 'en'
    })
    return response['link_token']

if __name__ == "__main__":
    user_id = "user_123"
    link_token = create_link_token(user_id)
    print(f"Generated Link Token: {link_token}")
