"""
Routes providing aggregated financial summary metrics.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from app.extensions import db
from app.models import Account, Transaction
from flask import Blueprint, jsonify, request
from sqlalchemy import case, func, or_

summary = Blueprint("summary", __name__)


def parse_date_range() -> Tuple[datetime, datetime]:
    """
    Parse start and end date from request args.
    Defaults to the last 30 days if not provided.
    """
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")

    if start_str:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    else:
        start_date = datetime.now().date() - timedelta(days=30)

    if end_str:
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    else:
        end_date = datetime.now().date()

    return start_date, end_date


def fetch_transaction_data(start_date: datetime, end_date: datetime):
    """
    Query daily aggregated income, expenses, and net totals within the date range.
    Filters hidden and internal accounts.
    """
    return (
        db.session.query(
            Transaction.date.label("date"),
            func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label(
                "income"
            ),
            func.sum(
                case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)
            ).label("expenses"),
            func.sum(Transaction.amount).label("net"),
        )
        .join(Account, Transaction.account_id == Account.account_id)
        .filter(
            or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)),
            or_(Transaction.is_internal.is_(False), Transaction.is_internal.is_(None)),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        )
        .group_by(Transaction.date)
        .order_by(Transaction.date)
        .all()
    )


def compute_daily_statistics(rows) -> Dict[str, Any]:
    """
    Compute aggregate totals and averages for daily income/expenses/net.
    """
    if not rows:
        return {
            "totalIncome": 0,
            "totalExpenses": 0,
            "totalNet": 0,
            "aboveAvgIncomeDays": 0,
            "aboveAvgExpenseDays": 0,
            "highestIncomeDay": None,
            "highestExpenseDay": None,
            "trend": 0,
            "volatility": 0,
            "outlierDates": [],
        }

    income_vals = [r.income or 0 for r in rows]
    expense_vals = [r.expenses or 0 for r in rows]
    net_vals = [r.net or 0 for r in rows]

    total_income = sum(income_vals)
    total_expenses = sum(expense_vals)
    total_net = sum(net_vals)
    days = len(rows)

    avg_income = total_income / days
    avg_expenses = total_expenses / days

    highest_income_idx = income_vals.index(max(income_vals))
    highest_expense_idx = expense_vals.index(max(expense_vals))

    return {
        "totalIncome": round(total_income, 2),
        "totalExpenses": round(total_expenses, 2),
        "totalNet": round(total_net, 2),
        "averageIncome": round(avg_income, 2),
        "averageExpenses": round(avg_expenses, 2),
        "highestIncomeDay": {
            "date": rows[highest_income_idx].date.isoformat(),
            "amount": income_vals[highest_income_idx],
        },
        "highestExpenseDay": {
            "date": rows[highest_expense_idx].date.isoformat(),
            "amount": expense_vals[highest_expense_idx],
        },
        "income_vals": income_vals,
        "expense_vals": expense_vals,
        "net_vals": net_vals,
        "days": days,
    }


def compute_volatility_metrics(stats: Dict[str, Any], rows) -> Dict[str, Any]:
    """
    Compute trend slope, volatility, and outlier detection using simple statistics.
    """
    n = stats["days"]
    net_vals = stats["net_vals"]

    x = list(range(n))
    sum_x = sum(x)
    sum_y = sum(net_vals)
    sum_xy = sum(x[i] * net_vals[i] for i in range(n))
    sum_xx = sum(xi * xi for xi in x)

    trend = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x) if n > 1 else 0

    mean_net = stats["totalNet"] / n
    variance = sum((v - mean_net) ** 2 for v in net_vals) / n
    volatility = variance**0.5 * 0.5
    threshold = 2 * volatility

    outlier_dates = [
        rows[i].date.isoformat()
        for i, v in enumerate(net_vals)
        if abs(v - mean_net) > threshold
    ]

    return {
        "trend": round(trend, 2),
        "volatility": round(volatility, 2),
        "outlierDates": outlier_dates,
    }


@summary.route("/financial", methods=["GET"])
def financial_summary():
    """
    REST endpoint: returns daily income, expense, and volatility summary.
    """
    try:
        start_date, end_date = parse_date_range()
        rows = fetch_transaction_data(start_date, end_date)
        stats = compute_daily_statistics(rows)

        # Merge volatility and trend metrics
        volatility_metrics = compute_volatility_metrics(stats, rows)
        stats.update(volatility_metrics)

        # Cleanup before returning (remove temp values)
        for k in ["income_vals", "expense_vals", "net_vals", "days"]:
            stats.pop(k, None)

        return jsonify({"status": "success", "data": stats}), 200

    except Exception as exc:  # Defensive: capture unexpected exceptions
        return jsonify({"status": "error", "message": str(exc)}), 500
