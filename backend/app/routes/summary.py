"""Routes providing aggregate financial summary metrics."""
from datetime import datetime, timedelta
from typing import Any, Dict

from app.extensions import db
from app.models import Account, Transaction
from flask import Blueprint, jsonify, request
from sqlalchemy import case, func, or_

summary = Blueprint("summary", __name__)


@summary.route("/financial", methods=["GET"])
def financial_summary() -> tuple[Any, int]:
    """Return income, expense and net statistics for the given date range."""
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = datetime.now().date()

        rows = (
            db.session.query(
                Transaction.date.label("date"),
                func.sum(
                    case((Transaction.amount > 0, Transaction.amount), else_=0)
                ).label("income"),
                func.sum(
                    case(
                        (Transaction.amount < 0, func.abs(Transaction.amount)), else_=0
                    )
                ).label("expenses"),
                func.sum(Transaction.amount).label("net"),
            )
            .join(Account, Transaction.account_id == Account.account_id)
            .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
            .filter(
                or_(
                    Transaction.is_internal.is_(False),
                    Transaction.is_internal.is_(None),
                )
            )
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .group_by(Transaction.date)
            .order_by(Transaction.date)
            .all()
        )

        if not rows:
            empty = {
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
            return jsonify({"status": "success", "data": empty}), 200

        income_vals = [r.income or 0 for r in rows]
        expense_vals = [r.expenses or 0 for r in rows]
        net_vals = [r.net or 0 for r in rows]

        total_income = sum(income_vals)
        total_expenses = sum(expense_vals)
        total_net = sum(net_vals)
        days = len(rows)

        avg_income = total_income / days
        avg_expenses = total_expenses / days
        above_income = sum(1 for v in income_vals if v > avg_income)
        above_expense = sum(1 for v in expense_vals if v > avg_expenses)

        max_income_idx = income_vals.index(max(income_vals))
        max_expense_idx = expense_vals.index(max(expense_vals))
        highest_income_day = {
            "date": rows[max_income_idx].date.isoformat(),
            "amount": income_vals[max_income_idx],
        }
        highest_expense_day = {
            "date": rows[max_expense_idx].date.isoformat(),
            "amount": expense_vals[max_expense_idx],
        }

        # Trend via simple linear regression slope
        n = days
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(net_vals)
        sum_xy = sum(x[i] * net_vals[i] for i in range(n))
        sum_xx = sum(xi * xi for xi in x)
        trend = (
            (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x) if n > 1 else 0
        )

        mean_net = total_net / days
        variance = sum((v - mean_net) ** 2 for v in net_vals) / days
        volatility = variance**0.5
        threshold = 2 * volatility
        outlier_dates = [
            rows[i].date.isoformat()
            for i, v in enumerate(net_vals)
            if abs(v - mean_net) > threshold
        ]

        data: Dict[str, Any] = {
            "totalIncome": round(total_income, 2),
            "totalExpenses": round(total_expenses, 2),
            "totalNet": round(total_net, 2),
            "aboveAvgIncomeDays": above_income,
            "aboveAvgExpenseDays": above_expense,
            "highestIncomeDay": highest_income_day,
            "highestExpenseDay": highest_expense_day,
            "trend": trend,
            "volatility": volatility,
            "outlierDates": outlier_dates,
        }
        return jsonify({"status": "success", "data": data}), 200

    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"status": "error", "message": str(exc)}), 500
