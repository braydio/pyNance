"""Charts API routes for financial dashboards."""

# TODO: move business logic to accounts_logic and transactions_logic modules
import traceback
from collections import defaultdict
from datetime import datetime, timedelta

from app.config import logger
from app.extensions import db
from app.models import Account, Category, Transaction
from app.services.forecast_orchestrator import ForecastOrchestrator
from app.utils.finance_utils import normalize_account_balance
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
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    root_category_id = request.args.get("category_id", None)
    top_n = request.args.get("top_n", 10, type=int)

    try:
        # Parse dates
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = datetime.now().date()

        # Fetch all categories and build mappings
        all_categories = db.session.query(Category).all()
        category_map = {cat.id: cat for cat in all_categories}
        child_map = {}
        for cat in all_categories:
            child_map.setdefault(cat.parent_id, []).append(cat.id)

        # Descendants helper (returns set of all child ids, including self)
        def get_descendant_ids(cat_id):
            ids = set([cat_id])
            to_visit = [cat_id]
            while to_visit:
                current = to_visit.pop()
                children = child_map.get(current, [])
                for child in children:
                    if child not in ids:
                        ids.add(child)
                        to_visit.append(child)
            return ids

        # Only true roots (parent_id is None)
        if root_category_id:
            try:
                root_category_id = int(root_category_id)
            except ValueError:
                return (
                    jsonify({"status": "error", "message": "Invalid category_id"}),
                    400,
                )
            root_ids = [root_category_id]
        else:
            root_ids = [cat.id for cat in all_categories if cat.parent_id is None]

        # Transactions filtered to the subtree of relevant root(s)
        all_cat_ids = set()
        for rid in root_ids:
            all_cat_ids |= get_descendant_ids(rid)

        txs = (
            db.session.query(Transaction)
            .join(Account, Transaction.account_id == Account.account_id)
            .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .filter(Transaction.category_id.in_(all_cat_ids))
            .all()
        )

        # Group txs by category id
        txs_by_cat = {}
        for tx in txs:
            txs_by_cat.setdefault(tx.category_id, []).append(tx)

        # Sum helper (sum for these category ids)
        def sum_for_catids(catids):
            return round(
                sum(abs(tx.amount) for cid in catids for tx in txs_by_cat.get(cid, [])),
                2,
            )

        # Labels
        def get_label(cat):
            if cat.parent_id is None:
                # Main category node
                return cat.primary_category or "Uncategorized"
            return cat.detailed_category or "Uncategorized"

        # Tree builder (main -> children)
        def build_tree(cat_id):
            cat = category_map[cat_id]
            children_ids = child_map.get(cat_id, [])
            # Only direct children!
            child_nodes = [build_tree(child_id) for child_id in children_ids]
            all_descendants = get_descendant_ids(cat_id)
            node = {
                "id": cat_id,
                "label": get_label(cat),
                "amount": sum_for_catids(all_descendants),
                "children": sorted(
                    child_nodes, key=lambda n: n["amount"], reverse=True
                ),
            }
            return node

        # Build root nodes, top_n filter
        root_nodes = [build_tree(rid) for rid in root_ids]
        root_nodes = sorted(root_nodes, key=lambda n: n["amount"], reverse=True)[:top_n]

        # Remove root nodes with zero sum
        root_nodes = [
            node
            for node in root_nodes
            if node["amount"] > 0
            or any(child["amount"] > 0 for child in node["children"])
        ]

        return jsonify(
            {
                "status": "success",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "data": root_nodes,
            }
        )

    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500
