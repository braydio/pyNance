# File: app/routes/charts.py
# business logic in this module (database / data fetching) should be moved to accounts_logic , transactions_logic
import traceback
from collections import defaultdict

from app.services.forecast_orchestrator import ForecastOrchestrator

from app.config import logger
from app.extensions import db
from app.models import Account, Category, Transaction
from app.utils.finance_utils import normalize_account_balance
from flask import Blueprint, jsonify, request

charts = Blueprint("charts", __name__)


@charts.route("/category_breakdown", methods=["GET"])
def category_breakdown():
    logger.debug("Entered category_breakdown endpoint")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    logger.debug(
        "Received query params - start_date: %s, end_date: %s",
        start_date_str,
        end_date_str,
    )

    try:
        if start_date_str:
            logger.debug("Parsing provided start_date: %s", start_date_str)
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)
            logger.debug(
                "No start_date provided; defaulting start_date to: %s", start_date
            )

        if end_date_str:
            logger.debug("Parsing provided end_date: %s", end_date_str)
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = datetime.now().date()
            logger.debug("No end_date provided; defaulting end_date to: %s", end_date)

        logger.debug("Querying transactions between %s and %s", start_date, end_date)
        transactions = (
            db.session.query(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id)
            .outerjoin(Account, Transaction.account_id == Account.account_id)
            .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .all()
        )
        logger.debug("Fetched %d transactions for processing", len(transactions))

        breakdown_map = {}
        for tx, category in transactions:
            key = category.display_name or "Uncategorized"
            amt = abs(tx.amount)

            if key not in breakdown_map:
                logger.debug("Initializing breakdown record for category: %s", key)
                breakdown_map[key] = {"amount": 0, "date": tx.date}
            breakdown_map[key]["amount"] += amt
            logger.debug(
                "Added %s to category '%s'. New cumulative amount: %s",
                amt,
                key,
                breakdown_map[key]["amount"],
            )
            if tx.date < breakdown_map[key]["date"]:
                logger.debug(
                    "Updating earliest transaction date for category '%s' from %s to %s",
                    key,
                    breakdown_map[key]["date"],
                    tx.date,
                )
                breakdown_map[key]["date"] = tx.date

        data = [
            {
                "category": k,
                "amount": round(v["amount"], 2),
                "date": v["date"],
            }
            for k, v in breakdown_map.items()
        ]
        logger.debug("Prepared final breakdown data: %s", data)

        logger.debug("Returning success response with data")
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

        transactions = (

            .join(Account, Transaction.account_id == Account.account_id)

            .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
        )
        if start_date:
            transactions = transactions.filter(Transaction.date >= start_date)
        if end_date:
            transactions = transactions.filter(Transaction.date <= end_date)

        all_tx = transactions.all()

        groups = {}
        for tx in all_tx:
            key = (
                tx.date.strftime("%Y-%m-%d")
                if granularity == "daily"
                else tx.date.strftime("%m-%Y")
            )
            amt = tx.amount
            if key not in groups:
                groups[key] = {"income": 0, "expenses": 0}
            if amt > 0:
                groups[key]["income"] += amt
            else:
                groups[key]["expenses"] += abs(amt)

        data = [
            {"date": k, "income": v["income"], "expenses": v["expenses"]}
            for k, v in sorted(groups.items())
        ]

        total_income = sum(item["income"] for item in data)
        total_expenses = sum(item["expenses"] for item in data)
        total_transactions = len(all_tx)

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
    today = datetime.utcnow().date()
    months = [today - timedelta(days=30 * i) for i in reversed(range(6))]

    data = []

    for month in months:
        accounts = (
            db.session.query(Account)
            .filter(Account.created_at <= month)
            .filter(Account.is_hidden.is_(False))
            .all()
        )

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

    return jsonify({"status": "success", "data": data}), 200

    return jsonify({"status": "success", "data": data}), 200

@charts.route("/daily_net", methods=["GET"])
def get_daily_net():
    try:
        logger.debug("Starting to retrieve daily net transactions.")
        today = datetime.now().date()
        logger.debug(f"Current date: {today}")
        start_date = today - timedelta(days=30)
        logger.debug(f"Calculating transactions from {start_date} to {today}.")

        transactions = (
            db.session.query(Transaction)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter(Account.is_hidden.is_(False))
            .filter(Transaction.date >= start_date)
            .all()
        )
        logger.debug(f"Retrieved {len(transactions)} transactions from the database.")

        day_map = {}
        for tx in transactions:
            day_str = tx.date.strftime("%Y-%m-%d")
            logger.debug(f"Processing transaction {tx.id} on date {day_str}.")

            # Safe access and fallback
            account = getattr(tx, "account", None)
            if not account or getattr(account, "subtype", None) is None:
                logger.warning(
                    f"Missing subtype for transaction {tx.id} on {tx.date}; defaulting to raw amount."
                )
            amt = tx.amount

            if day_str not in day_map:
                day_map[day_str] = {
                    "net": 0,
                    "income": 0,
                    "expenses": 0,
                    "transaction_count": 0,
                }
                logger.debug(f"Initializing entry for {day_str} in day_map.")

            day_map[day_str]["transaction_count"] += 1
            if amt > 0:
                day_map[day_str]["income"] += amt
                logger.debug(f"Adding to income for {day_str}: {amt}")
            else:
                day_map[day_str]["expenses"] += abs(amt)
                logger.debug(f"Adding to expenses for {day_str}: {abs(amt)}")
            day_map[day_str]["net"] += amt
            logger.debug(f"Updated net for {day_str}: {day_map[day_str]['net']}")

        # Fill in missing days
        logger.debug("Filling in missing days for the last 30 days.")
        data = []
        current = start_date
        while current <= today:
            key = current.strftime("%Y-%m-%d")
            entry = day_map.get(
                key, {"net": 0, "income": 0, "expenses": 0, "transaction_count": 0}
            )
            data.append(
                {
                    "date": key,
                    "net": round(entry["net"], 2),
                    "income": round(entry["income"], 2),
                    "expenses": round(entry["expenses"], 2),
                    "transaction_count": entry["transaction_count"],
                }
            )
            logger.debug(f"Added data entry for {key}: {data[-1]}")
            current += timedelta(days=1)

        logger.debug("Finished constructing response data.")
        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        logger.error(f"Error in daily net: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


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
            day = p["date"].strftime("%Y-%m-%d") if hasattr(p["date"], "strftime") else str(p["date"])
            daily_totals[day] += p.get("balance", 0)

        labels = []
        forecast_line = []
        start = datetime.utcnow().date()
        for i in range(horizon):
            day = start + timedelta(days=i)
            labels.append(day.strftime("%b %d"))
            forecast_line.append(round(daily_totals.get(day.strftime("%Y-%m-%d"), 0), 2))

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
