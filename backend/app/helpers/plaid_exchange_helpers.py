def exchange_public_token_for_product(public_token, product):
    """
    Exchanges a public token through the Plaid API, and tags
    the result with the associated product type for storage.
    **Note: this is a restructured replacement for plaid_helpers.exchange_public_token**
    """
    from plaid import Client
    from backend.api.keys import plaid_client_keys

    client = Client(
        client_id=plaid_client_keys.get("user_id"),
        secret=plaid_client_keys.get("client_secret"),
        env=plaid_client_keys.get("env"),
    )

    resp = client.Items.item_public_token_exchange(public_token)
    access_token = resp.access_token
    item_id = resp.item_id
    return {"access_token": access_token, "item_id": item_id, "product": product}
