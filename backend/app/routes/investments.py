"""Endpoints for retrieving investment account information and data."""

from app.extensions import db
from app.models import InvestmentHolding, Security, InvestmentTransaction
from app.sql import investments_logic
from flask import Blueprint, jsonify, request

investments = Blueprint("investments", __name__)


@investments.route("/accounts", methods=["GET"])
def list_investment_accounts():
    """Return all accounts linked with the Plaid investments product."""
    accounts = investments_logic.get_investment_accounts()
    return jsonify({"status": "success", "data": accounts}), 200


@investments.route("/holdings", methods=["GET"])
def list_holdings():
    """List current holdings with basic security info."""
    q = (
        db.session.query(InvestmentHolding, Security)
        .join(Security, InvestmentHolding.security_id == Security.security_id)
    )
    results = []
    for holding, sec in q.all():
        results.append(
            {
                "account_id": holding.account_id,
                "security_id": holding.security_id,
                "quantity": holding.quantity,
                "cost_basis": holding.cost_basis,
                "institution_value": holding.institution_value,
                "as_of": holding.as_of.isoformat() if holding.as_of else None,
                "security": {
                    "name": sec.name,
                    "ticker_symbol": sec.ticker_symbol,
                    "type": sec.type,
                    "currency": sec.iso_currency_code,
                    "price": sec.institution_price,
                    "price_as_of": sec.institution_price_as_of.isoformat()
                    if sec.institution_price_as_of
                    else None,
                },
            }
        )
    return jsonify({"status": "success", "data": results}), 200


@investments.route("/transactions", methods=["GET"])
def list_investment_transactions():
    """Paginated list of investment transactions with optional filters.

    Query params:
    - page, page_size
    - account_id (optional)
    - security_id (optional)
    """
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 25))
    account_id = request.args.get("account_id")
    security_id = request.args.get("security_id")
    q = InvestmentTransaction.query
    if account_id:
        q = q.filter(InvestmentTransaction.account_id == account_id)
    if security_id:
        q = q.filter(InvestmentTransaction.security_id == security_id)
    q = q.order_by(InvestmentTransaction.date.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    data = [
        {
            "investment_transaction_id": t.investment_transaction_id,
            "account_id": t.account_id,
            "security_id": t.security_id,
            "date": t.date.isoformat() if t.date else None,
            "amount": t.amount,
            "price": t.price,
            "quantity": t.quantity,
            "subtype": t.subtype,
            "type": t.type,
            "name": t.name,
            "fees": t.fees,
            "iso_currency_code": t.iso_currency_code,
        }
        for t in items
    ]
    return jsonify({"status": "success", "data": {"transactions": data, "total": total}}), 200
