"""Financial summary API routes."""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from app.config import logger
from app.extensions import db
from app.models import Transaction
from app.utils.finance_utils import display_transaction_amount
from flask import Blueprint, jsonify, request

summary = Blueprint("summary", __name__)


def _calculate_trend(values: List[float]) -> float:
    """Return slope of a simple linear regression for the provided values."""
    n = len(values)
    if n < 2:
        return 0.0
    x = list(range(n))
    sum_x = sum(x)
    sum_y = sum(values)
    sum_xy = sum(xi * yi for xi, yi in zip(x, values))
    sum_xx = sum(xi * xi for xi in x)
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return 0.0
    return (n * sum_xy - sum_x * sum_y) / denominator


def _calculate_volatility(values: List[float]) -> float:
    """Return standard deviation of the provided values."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return variance**0.5


def _detect_outliers(values: List[float], dates: List[str]) -> List[str]:
    """Return dates where the net value deviates more than 2σ from the mean."""
    if not values:
        return []
    mean = sum(values) / len(values)
    std = _calculate_volatility(values)
    if std == 0:
        return []
    return [d for d, v in zip(dates, values) if abs(v - mean) > 2 * std]


@summary.route("/financial", methods=["GET"])
def financial_summary() -> Any:
    """Aggregate financial metrics for a date range.

    Query Parameters:
        start_date: optional ISO date string (YYYY-MM-DD)
        end_date: optional ISO date string (YYYY-MM-DD)

    Returns:
        JSON payload containing totals, highest income/expense days,
        trend slope, volatility, and outlier dates.
    """
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = (datetime.now() - timedelta(days=30)).date()
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = datetime.now().date()

    logger.info("[summary] start_date=%s end_date=%s", start_date, end_date)

    transactions = (
        db.session.query(Transaction)
        .filter(Transaction.date >= start_date)
        .filter(Transaction.date <= end_date)
        .filter(
            (Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None))
        )
        .all()
    )

    day_map: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"income": 0.0, "expenses": 0.0, "net": 0.0}
    )
    for tx in transactions:
        tx_date = tx.date if isinstance(tx.date, date) else tx.date.date()
        amount = display_transaction_amount(tx)
        d = day_map[tx_date.strftime("%Y-%m-%d")]
        if amount > 0:
            d["income"] += amount
        elif amount < 0:
            d["expenses"] += amount
        d["net"] += amount

    daily = []
    for day, values in sorted(day_map.items()):
        daily.append({"date": day, **values})

    total_income = sum(d["income"] for d in daily)
    total_expenses = sum(d["expenses"] for d in daily)
    total_net = sum(d["net"] for d in daily)

    highest_income = max(daily, key=lambda d: d["income"], default=None)
    highest_expense = min(daily, key=lambda d: d["expenses"], default=None)

    net_values = [d["net"] for d in daily]
    dates = [d["date"] for d in daily]
    trend = _calculate_trend(net_values)
    volatility = _calculate_volatility(net_values)
    outliers = _detect_outliers(net_values, dates)

    result = {
        "totalIncome": round(total_income, 2),
        "totalExpenses": round(total_expenses, 2),
        "totalNet": round(total_net, 2),
        "highestIncomeDay": {
            "date": highest_income["date"] if highest_income else None,
            "amount": round(highest_income["income"], 2) if highest_income else 0,
        },
        "highestExpenseDay": {
            "date": highest_expense["date"] if highest_expense else None,
            "amount": round(highest_expense["expenses"], 2) if highest_expense else 0,
        },
        "trend": trend,
        "volatility": volatility,
        "outliers": outliers,
    }

    return jsonify({"status": "success", "data": result}), 200
