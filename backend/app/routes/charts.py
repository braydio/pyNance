# File: app/routes/charts.py

import random
from datetime import datetime, timedelta

from app.config import logger
from app.extensions import db
from app.models import Account, Transaction
from flask import Blueprint, jsonify, request
from sqlalchemy import case, func

charts = Blueprint("charts", __name__)


@charts.route("/category_breakdown", methods=["GET"])
def get_category_breakdown():
    """
    Group negative transactions by category and return top 10 spending categories.
    """
    try:
        result = (
            db.session.query(
                Transaction.category,
                func.sum(func.abs(Transaction.amount)).label("total"),
            )
            .filter(Transaction.amount < 0)
            .group_by(Transaction.category)
            .order_by(func.sum(func.abs(Transaction.amount)).desc())
            .limit(10)
            .all()
        )

        breakdown = [
            {"category": cat if cat else "Uncategorized", "amount": round(total, 2)}
            for cat, total in result
        ]
        return jsonify({"status": "success", "data": breakdown}), 200

    except Exception as e:
        logger.error(f"Error in category breakdown: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/cash_flow", methods=["GET"])
def get_cash_flow():
    """
    Aggregate income and expenses by daily or monthly granularity.
    """
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

        if granularity == "daily":
            group_expr = func.strftime("%Y-%m-%d", Transaction.date)
        else:
            group_expr = func.strftime("%m-%Y", Transaction.date)
        period_label = group_expr.label("period")

        query = db.session.query(
            period_label,
            func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label(
                "income"
            ),
            func.sum(
                case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)
            ).label("expenses"),
        )
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        query = query.group_by(period_label).order_by(period_label)
        results = query.all()

        data = [
            {"date": period, "income": income, "expenses": expenses}
            for period, income, expenses in results
        ]
        total_income = sum(item["income"] for item in data)
        total_expenses = sum(item["expenses"] for item in data)
        total_transactions = db.session.query(Transaction)
        if start_date:
            total_transactions = total_transactions.filter(
                Transaction.date >= start_date
            )
        if end_date:
            total_transactions = total_transactions.filter(Transaction.date <= end_date)
        total_transactions = total_transactions.count()

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
    """
    Calculate net assets by summing all account balances and simulate historical net worth.
    """
    try:
        accounts = Account.query.all()
        net = sum(acc.balance if acc.balance is not None else 0 for acc in accounts)
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
        logger.error(f"Error in net assets: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@charts.route("/daily_net", methods=["GET"])
def get_daily_net():
    """
    Aggregate transactions for the past 30 days with daily net, income, expenses, and count.
    """
    try:
        today = datetime.now().date()
        start_date = today - timedelta(days=30)

        query = (
            db.session.query(
                func.strftime("%Y-%m-%d", Transaction.date).label("day"),
                func.sum(Transaction.amount).label("net"),
                func.sum(
                    case((Transaction.amount > 0, Transaction.amount), else_=0)
                ).label("income"),
                func.sum(
                    case(
                        (Transaction.amount < 0, func.abs(Transaction.amount)), else_=0
                    )
                ).label("expenses"),
                func.count(Transaction.transaction_id).label("transaction_count"),
            )
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= today)
            .group_by("day")
            .order_by("day")
        )
        results = query.all()

        results_dict = {
            day: {
                "net": net,
                "income": income,
                "expenses": expenses,
                "transaction_count": transaction_count,
            }
            for day, net, income, expenses, transaction_count in results
        }

        data = []
        current = start_date
        while current <= today:
            day_str = current.strftime("%Y-%m-%d")
            daily = results_dict.get(
                day_str, {"net": 0, "income": 0, "expenses": 0, "transaction_count": 0}
            )
            data.append(
                {
                    "date": day_str,
                    "net": round(daily["net"], 2),
                    "income": round(daily["income"], 2),
                    "expenses": round(daily["expenses"], 2),
                    "transaction_count": daily["transaction_count"],
                }
            )
            current += timedelta(days=1)

        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        logger.error(f"Error in daily net: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
