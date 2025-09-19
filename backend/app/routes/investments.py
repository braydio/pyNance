"""Endpoints for retrieving investment account information and data."""

from datetime import date, datetime
from typing import Dict, Mapping, Optional

from app.extensions import db
from app.models import InvestmentHolding, InvestmentTransaction, Security
from app.sql import investments_logic
from flask import Blueprint, jsonify, request

investments = Blueprint("investments", __name__)


DATE_PARAM_FORMAT = "%Y-%m-%d"


def parse_transaction_filter_params(
    args: Mapping[str, str],
) -> Dict[str, Optional[str | date]]:
    """Parse and validate optional filter params for investment transactions.

    Args:
        args: Mapping of query parameters from the incoming request.

    Returns:
        Dictionary containing the normalized filters with `date` objects for
        date fields and raw strings for identity filters.

    Raises:
        ValueError: If the provided date parameters are not ISO formatted or if
        ``end_date`` is before ``start_date``.
    """

    account_id = args.get("account_id") or None
    security_id = args.get("security_id") or None
    txn_type = args.get("type") or None
    subtype = args.get("subtype") or None

    start_date_raw = args.get("start_date") or None
    end_date_raw = args.get("end_date") or None

    start_date = _parse_iso_date(start_date_raw) if start_date_raw else None
    end_date = _parse_iso_date(end_date_raw) if end_date_raw else None

    if start_date and end_date and end_date < start_date:
        raise ValueError("end_date must be greater than or equal to start_date")

    return {
        "account_id": account_id,
        "security_id": security_id,
        "type": txn_type,
        "subtype": subtype,
        "start_date": start_date,
        "end_date": end_date,
    }


def _parse_iso_date(value: str) -> date:
    """Convert an ISO ``YYYY-MM-DD`` string to a :class:`datetime.date`.

    Args:
        value: String representation of the date.

    Returns:
        Parsed :class:`datetime.date` instance.

    Raises:
        ValueError: If the input is not parseable using the expected format.
    """

    try:
        return datetime.strptime(value, DATE_PARAM_FORMAT).date()
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(
            f"Invalid date '{value}'. Expected format YYYY-MM-DD."
        ) from exc


@investments.route("/accounts", methods=["GET"])
def list_investment_accounts():
    """Return all accounts linked with the Plaid investments product."""
    accounts = investments_logic.get_investment_accounts()
    return jsonify({"status": "success", "data": accounts}), 200


@investments.route("/holdings", methods=["GET"])
def list_holdings():
    """List current holdings with basic security info."""
    q = db.session.query(InvestmentHolding, Security).join(
        Security, InvestmentHolding.security_id == Security.security_id
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
                    "price_as_of": (
                        sec.institution_price_as_of.isoformat()
                        if sec.institution_price_as_of
                        else None
                    ),
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
    - type (optional)
    - subtype (optional)
    - start_date / end_date (optional, ISO ``YYYY-MM-DD``)
    """
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 25))

    try:
        filters = parse_transaction_filter_params(request.args)
    except ValueError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400

    q = InvestmentTransaction.query
    account_id = filters["account_id"]
    if account_id:
        q = q.filter(InvestmentTransaction.account_id == account_id)
    security_id = filters["security_id"]
    if security_id:
        q = q.filter(InvestmentTransaction.security_id == security_id)
    txn_type = filters["type"]
    if txn_type:
        q = q.filter(InvestmentTransaction.type == txn_type)
    subtype = filters["subtype"]
    if subtype:
        q = q.filter(InvestmentTransaction.subtype == subtype)
    start_date = filters["start_date"]
    if start_date:
        q = q.filter(InvestmentTransaction.date >= start_date)
    end_date = filters["end_date"]
    if end_date:
        q = q.filter(InvestmentTransaction.date <= end_date)
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
    response_payload = {
        "transactions": data,
        "total": total,
        "filters": {
            "account_id": account_id,
            "security_id": security_id,
            "type": txn_type,
            "subtype": subtype,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    }
    return jsonify({"status": "success", "data": response_payload}), 200
