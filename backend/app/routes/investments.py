"""Endpoints for retrieving investment account information."""

from app.sql import investments_logic
from flask import Blueprint, jsonify

investments = Blueprint("investments", __name__)


@investments.route("/accounts", methods=["GET"])
def list_investment_accounts():
    """Return all accounts linked with the Plaid investments product."""
    accounts = investments_logic.get_investment_accounts()
    return jsonify({"status": "success", "data": accounts}), 200
