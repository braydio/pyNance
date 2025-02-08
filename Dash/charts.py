import json
import random
from datetime import datetime, timedelta

from config import FILES, logger
from flask import Blueprint, jsonify
from helper_utils import load_json

TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
LINKED_ACCOUNTS = FILES["LINKED_ACCOUNTS"]

charts = Blueprint("charts", __name__)


@charts.route("/api/category_breakdown", methods=["GET"])
def get_category_breakdown():
    try:
        transactions = load_json(TRANSACTIONS_LIVE).get("transactions", [])
        category_data = {}
        for tx in transactions:
            category = tx.get("category", ["Uncategorized"])
            if isinstance(category, list) and category:
                category = category[0]
            amount = tx.get("amount")
            if amount is not None and isinstance(amount, (int, float)) and amount < 0:
                category_data[category] = category_data.get(category, 0) + abs(amount)
        category_breakdown = [
            {"category": cat, "amount": round(amt, 2)}
            for cat, amt in category_data.items()
        ]
        return jsonify({"status": "success", "data": category_breakdown}), 200

    except FileNotFoundError:
        logger.error("TRANSACTIONS_LIVE file not found.")
        return (
            jsonify({"status": "error", "message": "Transactions file not found."}),
            404,
        )
    except json.JSONDecodeError:
        logger.error("Error decoding TRANSACTIONS_LIVE.")
        return (
            jsonify(
                {"status": "error", "message": "Invalid transactions file format."}
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Error in category breakdown: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/api/cash_flow", methods=["GET"])
def get_cash_flow():
    try:
        transactions = load_json(TRANSACTIONS_LIVE).get("transactions", [])
        monthly_cash_flow = {}
        for tx in transactions:
            try:
                date = datetime.strptime(tx["date"], "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Skipping transaction with invalid date: {tx}")
                continue

            month_year = f"{date.strftime('%B')} {date.year}"
            if month_year not in monthly_cash_flow:
                monthly_cash_flow[month_year] = {"income": 0, "expenses": 0}

            if "amount" not in tx or not isinstance(tx["amount"], (int, float)):
                logger.warning(f"Skipping invalid transaction: {tx}")
                continue

            if tx["amount"] > 0:
                monthly_cash_flow[month_year]["income"] += tx["amount"]
            else:
                monthly_cash_flow[month_year]["expenses"] += abs(tx["amount"])

        data = [
            {"month": month, **values}
            for month, values in sorted(
                monthly_cash_flow.items(),
                key=lambda x: datetime.strptime(x[0], "%B %Y"),
            )
        ]
        total_income = sum(values["income"] for values in monthly_cash_flow.values())
        total_expenses = sum(
            values["expenses"] for values in monthly_cash_flow.values()
        )

        return jsonify(
            {
                "status": "success",
                "data": data,
                "metadata": {
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "total_transactions": len(transactions),
                },
            }
        )

    except FileNotFoundError:
        logger.error("TRANSACTIONS_LIVE file not found.")
        return (
            jsonify({"status": "error", "message": "Transactions file not found."}),
            404,
        )
    except json.JSONDecodeError:
        logger.error("Error decoding TRANSACTIONS_LIVE.")
        return (
            jsonify(
                {"status": "error", "message": "Invalid transactions file format."}
            ),
            400,
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/api/net_assets", methods=["GET"])
def get_net_assets():
    try:
        with open(LINKED_ACCOUNTS, "r") as f:
            linked_accounts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.error("LinkedAccounts.json missing or invalid.")
        return jsonify({"status": "error", "message": "No accounts found."}), 404

    current_net_worth = 0
    for item_id, account_data in linked_accounts.items():
        bal = account_data.get("balances", {}).get("current", 0)
        if account_data.get("type") == "credit":
            bal *= -1
        current_net_worth += bal

    data = []
    base_date = datetime.now().replace(day=1)
    running_value = current_net_worth - random.randint(500, 5000)
    for months_ago in range(6, -1, -1):
        date_obj = base_date - timedelta(days=30 * months_ago)
        variation = random.randint(-2000, 3000)
        running_value += variation
        if months_ago == 0:
            running_value = current_net_worth
        data.append(
            {"date": date_obj.strftime("%Y-%m-%d"), "netWorth": round(running_value, 2)}
        )

    return jsonify({"status": "success", "data": data}), 200
