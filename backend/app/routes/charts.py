# app/routes/charts.py
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from app.config import FILES, logger

from flask import Blueprint, jsonify, request

charts = Blueprint("charts", __name__)


def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            resolved_path = Path(file_path).resolve()
            logger.debug(f"Loaded from {resolved_path}")
            return json.load(f)
    return {}


def load_json_safe(file_path):
    """
    Load JSON from the given file. Returns a tuple (data, error) where
    data is the loaded JSON (or {} if errors occur) and error is None or
    a descriptive error message.
    """
    if not os.path.exists(file_path):
        err = f"File not found: {file_path}"
        logger.error(err)
        return {}, err
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Loaded data from {Path(file_path).resolve()}")
        return data, None
    except json.JSONDecodeError as e:
        err = f"JSON decode error in {file_path}: {e}"
        logger.error(err, exc_info=True)
        return {}, err
    except Exception as e:
        err = f"Error reading {file_path}: {e}"
        logger.error(err, exc_info=True)
        return {}, err


@charts.route("/category_breakdown", methods=["GET"])
def get_category_breakdown():
    try:
        transactions = load_json(FILES["TRANSACTIONS_LIVE"]).get("transactions", [])
        category_data = {}
        for tx in transactions:
            cat = tx.get("category", ["Uncategorized"])
            if isinstance(cat, list) and cat:
                cat = cat[0]
            amount = tx.get("amount")
            if isinstance(amount, (int, float)) and amount < 0:
                category_data[cat] = category_data.get(cat, 0) + abs(amount)
        breakdown = [
            {"category": k, "amount": round(v, 2)} for k, v in category_data.items()
        ]
        return jsonify({"status": "success", "data": breakdown}), 200
    except Exception as e:
        logger.error(f"Error in category breakdown: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/cash_flow", methods=["GET"])
def get_cash_flow():
    try:
        granularity = request.args.get("granularity", "monthly")
        transactions = load_json(FILES["TRANSACTIONS_LIVE"]).get("transactions", [])
        cash_flow = {}
        for tx in transactions:
            try:
                dt = datetime.strptime(tx["date"], "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Skipping invalid date: {tx}")
                continue

            if granularity == "daily":
                key = dt.strftime("%Y-%m-%d")
            else:  # Default to monthly
                key = f"{dt.strftime('%B')} {dt.year}"

            cash_flow.setdefault(key, {"income": 0, "expenses": 0})
            if tx["amount"] > 0:
                cash_flow[key]["income"] += tx["amount"]
            else:
                cash_flow[key]["expenses"] += abs(tx["amount"])

        data = [
            {"date": k, **v}
            for k, v in sorted(
                cash_flow.items(),
                key=lambda x: datetime.strptime(
                    x[0], "%Y-%m-%d" if granularity == "daily" else "%B %Y"
                ),
            )
        ]
        total_income = sum(v["income"] for v in cash_flow.values())
        total_expenses = sum(v["expenses"] for v in cash_flow.values())
        return (
            jsonify(
                {
                    "status": "success",
                    "data": data,
                    "metadata": {
                        "total_income": total_income,
                        "total_expenses": total_expenses,
                        "total_transactions": len(transactions),
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error in cash flow: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/net_assets", methods=["GET"])
def get_net_assets():
    try:
        with open(FILES["LINKED_ACCOUNTS"], "r") as f:
            linked_accounts = json.load(f)
        net = 0
        for acc in linked_accounts.values():
            bal = acc.get("balances", {}).get("current", 0)
            if acc.get("type") == "credit":
                bal *= -1
            net += bal

        # Create dummy historical data for illustration.
        base_date = datetime.now().replace(day=1)
        running = net - random.randint(500, 5000)
        data = []
        for m in range(6, -1, -1):
            dt = base_date - timedelta(days=30 * m)
            variation = random.randint(-2000, 3000)
            running += variation
            if m == 0:
                running = net
            data.append(
                {"date": dt.strftime("%Y-%m-%d"), "netWorth": round(running, 2)}
            )
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Error in net assets: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
