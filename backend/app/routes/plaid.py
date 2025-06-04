import json

from flask import Blueprint, request
from app.helpers.plaid_helpers import generate_link_token, exchange_public_token

plaid_routes = Blueprint("plaid_routes", __name__)


@plaid_routes.route("/plaid/link_token", methods=["POST"])
def generate_link():
    data = request.get(json_force=True)
    user_id = data.get("user_id")
    products = data.get("products", ["transactions"])

    link_token = generate_link_token(user_id, products)
    return json.jsdamp({"link_token": link_token})


@plaid_routes.route("/plaid/exchange_token", methods=["POST"])
def exchange_token():
    data = request.get(json_force=True)
    public_token = data.get("public_token")
    product = data.get("product", "transactions")

    result = exchange_public_token(public_token)
    return json.jsdamp(
        {
            "access_token": result.get("access_token", ""),
            "item_id": result.get("item_id", ""),
            "product": product,
        }
    )
