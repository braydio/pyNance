"""Charts API routes for financial dashboards."""

# TODO: move business logic to accounts_logic and transactions_logic modules
import traceback
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict

from app.config import logger
from app.extensions import db
from app.models import Account, Category, Transaction
from app.services.forecast_orchestrator import ForecastOrchestrator
from app.utils.finance_utils import (
    display_transaction_amount,
    normalize_account_balance,
)
from flask import Blueprint, jsonify, request
from sqlalchemy import case, func

charts = Blueprint("charts", __name__)


@charts.route("/category_breakdown", methods=["GET"])
def category_breakdown():
    logger.debug("Entered category_breakdown endpoint")

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)
            logger.debug("No start_date provided; defaulting to: %s", start_date)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = datetime.now().date()
            logger.debug("No end_date provided; defaulting to: %s", end_date)

        logger.debug("Querying transactions between %s and %s", start_date, end_date)

        transactions = (
            db.session.query(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .distinct(Transaction.id)
            .all()
        )

        logger.debug("Fetched %d transactions for processing", len(transactions))

        breakdown_map = {}

        for tx, category in transactions:
            key = getattr(category, "display_name", None) or "Uncategorized"
            amount = abs(tx.amount)

            if key not in breakdown_map:
                logger.debug("Initializing breakdown record for category: %s", key)
                breakdown_map[key] = {"amount": 0, "date": tx.date}

            breakdown_map[key]["amount"] += amount
            if tx.date < breakdown_map[key]["date"]:
                logger.debug(
                    "Updating earliest transaction date for category '%s' from %s to %s",
                    key,
                    breakdown_map[key]["date"],
                    tx.date,
                )
                breakdown_map[key]["date"] = tx.date

        # Sort by descending amount
        sorted_items = sorted(
            breakdown_map.items(), key=lambda item: item[1]["amount"], reverse=True
        )

        data = [
            {
                "category": k,
                "amount": round(v["amount"], 2),
                "date": v["date"].isoformat(),
            }
            for k, v in sorted_items
        ]

        logger.debug("Prepared final breakdown data: %s", data)
        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        logger.error("Error in category_breakdown endpoint: %s", e, exc_info=True)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/cash_flow", methods=["GET"])
def get_cash_flow():
    try:
        granularity = request.args.get("granularity", "monthly")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        )

        date_fmt = "%Y-%m-%d" if granularity == "daily" else "%m-%Y"
        date_expr = func.strftime(date_fmt, Transaction.date).label("period")

        income_sum = func.sum(
            case((Transaction.amount > 0, Transaction.amount), else_=0)
        ).label("income")
        expense_sum = func.sum(
            case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)
        ).label("expenses")
        tx_count = func.count(Transaction.id).label("txn_count")

        aggregated = (
            db.session.query(date_expr, income_sum, expense_sum, tx_count)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
        )
        if start_date:
            aggregated = aggregated.filter(Transaction.date >= start_date)
        if end_date:
            aggregated = aggregated.filter(Transaction.date <= end_date)

        rows = aggregated.group_by(date_expr).order_by(date_expr).all()

        data = [
            {
                "date": row.period,
                "income": row.income or 0,
                "expenses": row.expenses or 0,
            }
            for row in rows
        ]

        total_income = sum(row.income or 0 for row in rows)
        total_expenses = sum(row.expenses or 0 for row in rows)
        total_transactions = sum(row.txn_count or 0 for row in rows)

        return (
            jsonify(
                {
                    "status": "success",
                    "data": data,
                    "metadata": {
                        "total_income": total_income,
                        "total_expenses": total_expenses,
                        "total_transactions": total_transactions,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error in cash flow: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/net_assets", methods=["GET"])
def get_net_assets():
    """Return trended net asset values.

    Balances are normalized so liabilities reduce net worth while assets
    increase it. The response is wrapped in a ``{"status": "success", "data": ...}``
    payload for frontend consumption.
    """
    # Use non-deprecated current date
    today = datetime.now().date()
    months = [today - timedelta(days=30 * i) for i in reversed(range(6))]

    logger.debug("Computing net assets for months: %s", months)

    data = []

    for month in months:
        accounts = db.session.query(Account).filter(Account.is_hidden.is_(False)).all()
        logger.debug("Month %s - retrieved %d accounts", month, len(accounts))

        net = sum(
            normalize_account_balance(
                acc.balance if acc.balance is not None else 0, acc.type
            )
            for acc in accounts
        )

        assets = sum(
            acc.balance
            for acc in accounts
            if acc.type.lower() not in ["credit", "loan", "liability"]
            and acc.balance is not None
        )

        liabilities = sum(
            acc.balance
            for acc in accounts
            if acc.type.lower() in ["credit", "credit card", "loan", "liability"]
            and acc.balance is not None
        )

        data.append(
            {
                "date": month.isoformat(),
                "net_assets": net,
                "assets": assets,
                "liabilities": liabilities,
            }
        )
        logger.debug(
            "Appended net asset record for %s: net=%s, assets=%s, liabilities=%s",
            month.isoformat(),
            net,
            assets,
            liabilities,
        )
    return jsonify({"status": "success", "data": data}), 200


@charts.route("/daily_net", methods=["GET"])
def get_daily_net() -> Dict[str, Dict[str, Any]]:
    """
    Returns a dict mapping YYYY-MM-DD string to:
      {
        "date": str,
        "income": { "source": str, "parsedValue": float },
        "expenses": { "source": str, "parsedValue": float },
        "net": { "source": str, "parsedValue": float },
        "transaction_count": int
      }
    All amounts are floats. Income is always positive. Expenses are always negative.
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # Default to last 30 days if not provided
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = (datetime.now() - timedelta(days=30)).date()
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = datetime.now().date()

    logger.info(f"[daily_net] start_date={start_date}, end_date={end_date}")

    transactions = (
        db.session.query(Transaction)
        .filter(Transaction.date >= start_date)
        .filter(Transaction.date <= end_date)
        .all()
    )

    logger.info(f"[daily_net] Transaction count in date range: {len(transactions)}")

    day_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "date": "",
            "income": 0.0,
            "expenses": 0.0,
            "net": 0.0,
            "transaction_count": 0,
        }
    )

    for tx in transactions:
        tx_date = tx.date if isinstance(tx.date, date) else tx.date.date()
        day_str = tx_date.strftime("%Y-%m-%d")
        # Normalize transaction amount for UI: expenses negative, income positive
        amount = display_transaction_amount(tx)

        d = day_map[day_str]
        d["date"] = day_str
        d["transaction_count"] += 1

        # Positive amounts are income; negative amounts are expenses
        if amount > 0:
            d["income"] += amount
        elif amount < 0:
            d["expenses"] += amount
        d["net"] += amount

    # Format results into a list of day buckets
    data = []
    for day in sorted(day_map.keys()):
        v = day_map[day]
        data.append(
            {
                "date": v["date"],
                "income": {
                    "source": str(round(v["income"], 2)),
                    "parsedValue": round(v["income"], 2),
                },
                "expenses": {
                    "source": str(round(v["expenses"], 2)),
                    "parsedValue": round(v["expenses"], 2),
                },
                "net": {
                    "source": str(round(v["net"], 2)),
                    "parsedValue": round(v["net"], 2),
                },
                "transaction_count": v["transaction_count"],
            }
        )

    logger.info(f"[daily_net] Returning {len(data)} day buckets")
    # Return a consistent payload for frontend consumption
    return jsonify({"status": "success", "data": data}), 200


@charts.route("/accounts-snapshot", methods=["GET"])
def accounts_snapshot():
    user_id = request.args.get("user_id")
    accounts = (
        db.session.query(Account)
        .filter(Account.user_id == user_id)
        .filter(Account.is_hidden.is_(False))
        .order_by(Account.balance.desc())
        .all()
    )

    result = [
        {
            "account_id": acc.account_id,
            "name": acc.name,
            "institution_name": acc.institution_name,
            "balance": normalize_account_balance(acc.balance, acc.type),
            "type": acc.type,
            "subtype": acc.subtype,
        }
        for acc in accounts
    ]
    return jsonify(result)


@charts.route("/forecast", methods=["GET", "POST"])
def forecast_route():
    """Return forecast vs actual lines for the authenticated user."""
    try:
        view_type = request.args.get("view_type", "Month")
        manual_income = float(request.args.get("manual_income", 0))
        liability_rate = float(request.args.get("liability_rate", 0))

        horizon = 30 if view_type.lower() == "month" else 365

        orchestrator = ForecastOrchestrator(db.session)
        projections = orchestrator.forecast(days=horizon)

        daily_totals = defaultdict(float)
        for p in projections:
            day = (
                p["date"].strftime("%Y-%m-%d")
                if hasattr(p["date"], "strftime")
                else str(p["date"])
            )
            daily_totals[day] += p.get("balance", 0)

        labels = []
        forecast_line = []
        # Use non-deprecated current date for forecast labels
        start = datetime.now().date()
        for i in range(horizon):
            day = start + timedelta(days=i)
            labels.append(day.strftime("%b %d"))
            forecast_line.append(
                round(daily_totals.get(day.strftime("%Y-%m-%d"), 0), 2)
            )

        adjustment = manual_income - liability_rate
        if adjustment:
            forecast_line = [round(f + adjustment, 2) for f in forecast_line]

        actuals = [None for _ in range(horizon)]

        metadata = {
            "account_count": len({p["account_id"] for p in projections}),
            "recurring_count": 0,
            "data_age_days": 0,
        }

        return (
            jsonify(
                {
                    "labels": labels,
                    "forecast": forecast_line,
                    "actuals": actuals,
                    "metadata": metadata,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error generating forecast: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/category_breakdown_tree", methods=["GET"])
def category_breakdown_tree():
    """
    Returns expense breakdown by parent category (primary_category, one bar per parent),
    with bar segments for each detailed_category (stacked).
    Only negative (expense) transactions are counted, using display_transaction_amount
    to ensure consistent signage regardless of account or transaction type.
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    top_n = request.args.get("top_n", 10, type=int)

    try:
        # Date parsing, fallback to last 30 days
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = datetime.now().date()

        # Aggregate: {primary_category: {"amount": sum, "children": {detailed_category: sum}}}
        category_breakdown = defaultdict(
            lambda: {"amount": 0, "children": defaultdict(float)}
        )

        # Query all relevant transactions (category join for label, account join for normalization)
        transactions = (
            db.session.query(Transaction)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .all()
        )

        transactions = (
            db.session.query(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .all()
        )
        for tx, cat in transactions:
            if not cat:
                continue
            amount = display_transaction_amount(tx)
            if amount >= 0:
                continue
            parent_label = cat.primary_category or "Uncategorized"
            child_label = cat.detailed_category or "Other"

            amt = abs(amount)
            category_breakdown[parent_label]["amount"] += amt
            category_breakdown[parent_label]["children"][child_label] += amt

        # Compose output: one bar per primary_category
        output = []
        for parent_label, data in category_breakdown.items():
            children = [
                {"label": child, "amount": round(amount, 2)}
                for child, amount in sorted(
                    data["children"].items(), key=lambda x: x[1], reverse=True
                )
            ]
            output.append(
                {
                    "label": parent_label,
                    "amount": round(data["amount"], 2),
                    "children": children,
                }
            )

        # Top-N by spending
        output_sorted = sorted(output, key=lambda x: x["amount"], reverse=True)[:top_n]

        logger.debug("Category breakdown output (primary/detailed): %s", output_sorted)
        return (
            jsonify(
                {
                    "status": "success",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "data": output_sorted,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Error in category_breakdown_tree: %s", e, exc_info=True)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
