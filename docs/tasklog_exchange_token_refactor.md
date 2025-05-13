# Tasklog: Exchange Token Refactor
`by: Arch Linux Assistant
date: 2025-05-13
repo : pyNance
checklist:
  - X Review accounts_link_api.pi and frontend/src/api/accounts_link.js
  - X Verify that link_token route supports multiple products
  - [] Extract product token handling to new helper module: plaid_exchange_helpers.py
  - [] Schema logged to /docs/plaid_product_response_schema.json
  - X Update roadmap in Canvas with new function definition
  - X Function added to plaid_exchange_helpers.py:
`code^
`def
exchange_public_token_for_product(public_token, product):
    from plaid import Client
    from backend.api.keys import plaid_client_keys
    client = Client(
        client_id=plaid_client_keys.get("user_id"),
        secret=plaid_client_keys.get("client_secret"),
        env=plaid_client_keys.get("env")
    )
    resp = client.Items.item_public_token_exchange(public_token)
    return {
      "access_token": resp.access_token,
      "item_id": resp.item_id,
      "product": product
    }
```