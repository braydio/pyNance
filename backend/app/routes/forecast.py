from datetime import date, datetime, timedelta

from app.config import logger
from app.extensions import db
from app.models import Account, AccountHistory, Transaction
from app.services.forecast_orchestrator import ForecastOrchestrator
from flask import Blueprint, jsonify, request
from forecast.engine import compute_forecast
from sqlalchemy import case, func

forecast = Blueprint("forecast", __name__)
LOOKBACK_DAYS = 90


def _parse_account_filters(
    payload: dict[str, object],
) -> tuple[list[str] | None, list[str]]:
    """Normalize include/exclude account filters from a compute payload.

    Returns:
        A tuple of ``(included_account_ids, excluded_account_ids)`` where
        ``included_account_ids`` is ``None`` when no explicit inclusion list was
        provided.
    """

    included_raw = payload.get("included_account_ids")
    excluded_raw = payload.get("excluded_account_ids")

    if included_raw is not None and not isinstance(included_raw, list):
        raise ValueError("included_account_ids must be a list.")
    if excluded_raw is not None and not isinstance(excluded_raw, list):
        raise ValueError("excluded_account_ids must be a list.")

    included_ids = (
        [str(account_id) for account_id in included_raw if str(account_id).strip()]
        if isinstance(included_raw, list)
        else None
    )
    excluded_ids = (
        [str(account_id) for account_id in excluded_raw if str(account_id).strip()]
        if isinstance(excluded_raw, list)
        else []
    )

    if included_ids is not None:
        deduped: list[str] = []
        for account_id in included_ids:
            if account_id not in deduped:
                deduped.append(account_id)
        included_ids = deduped

    deduped_excluded: list[str] = []
    for account_id in excluded_ids:
        if account_id not in deduped_excluded:
            deduped_excluded.append(account_id)

    return included_ids, deduped_excluded


def _parse_start_date(raw_value: str | None) -> date:
    """Parse an ISO date string into a date instance with a fallback to today."""
    if not raw_value:
        return date.today()
    try:
        return datetime.fromisoformat(raw_value).date()
    except ValueError as exc:
        raise ValueError("start_date must be ISO-8601 formatted (YYYY-MM-DD).") from exc


def _parse_horizon_days(raw_value: object) -> int:
    """Normalize the horizon_days value into a positive integer."""
    if raw_value is None:
        return 30
    try:
        horizon = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("horizon_days must be an integer.") from exc
    if horizon <= 0:
        raise ValueError("horizon_days must be greater than zero.")
    return horizon


def _parse_moving_average_window(raw_value: object) -> int:
    """Normalize moving average window values accepted by compute API."""
    if raw_value is None:
        return 30
    try:
        window = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("moving_average_window must be an integer.") from exc
    if window not in {7, 30, 60, 90}:
        raise ValueError("moving_average_window must be one of 7, 30, 60, or 90.")
    return window


def _parse_graph_mode(raw_value: object) -> str:
    """Normalize graph mode values used by forecast chart controls."""
    if raw_value is None:
        return "combined"
    graph_mode = str(raw_value).strip().lower()
    if graph_mode not in {"combined", "forecast", "historical"}:
        raise ValueError("graph_mode must be one of combined, forecast, or historical.")
    return graph_mode


def _parse_normalize(raw_value: object) -> bool:
    """Normalize truthy payload values for historical normalization."""
    if isinstance(raw_value, bool):
        return raw_value
    if raw_value is None:
        return False
    if isinstance(raw_value, str):
        if raw_value.strip().lower() in {"true", "1", "yes"}:
            return True
        if raw_value.strip().lower() in {"false", "0", "no"}:
            return False
    raise ValueError("normalize must be a boolean.")


def _load_latest_snapshots(
    user_id: str,
    included_account_ids: list[str] | None = None,
    excluded_account_ids: list[str] | None = None,
) -> list[dict[str, object]]:
    """Return the most recent balance snapshot for each visible account."""
    included_ids = included_account_ids or []
    excluded_ids = excluded_account_ids or []

    accounts_query = db.session.query(Account).filter(
        (Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None))
    )
    if user_id:
        accounts_query = accounts_query.filter(Account.user_id == user_id)
    if included_ids:
        accounts_query = accounts_query.filter(Account.account_id.in_(included_ids))
    if excluded_ids:
        accounts_query = accounts_query.filter(~Account.account_id.in_(excluded_ids))
    accounts = accounts_query.all()

    account_ids = [account.account_id for account in accounts]
    latest_history = []
    if account_ids:
        subquery = (
            db.session.query(
                AccountHistory.account_id,
                func.max(AccountHistory.date).label("max_date"),
            )
            .filter(AccountHistory.account_id.in_(account_ids))
            .group_by(AccountHistory.account_id)
            .subquery()
        )
        latest_history = (
            db.session.query(AccountHistory)
            .join(
                subquery,
                (AccountHistory.account_id == subquery.c.account_id)
                & (AccountHistory.date == subquery.c.max_date),
            )
            .all()
        )

    history_by_account = {row.account_id: row for row in latest_history}
    today = date.today()
    snapshots = []
    for account in accounts:
        history = history_by_account.get(account.account_id)
        if history:
            balance = float(history.balance)
            snapshot_date = history.date
        else:
            balance = float(account.balance)
            snapshot_date = today
        snapshots.append(
            {
                "account_id": account.account_id,
                "user_id": account.user_id,
                "balance": balance,
                "date": snapshot_date,
                "account_type": account.account_type,
                "is_investment": bool(account.is_investment),
                "investment_has_holdings": bool(account.investment_has_holdings),
                "investment_has_transactions": bool(
                    account.investment_has_transactions
                ),
            }
        )

    return snapshots


def _load_historical_aggregates(
    user_id: str,
    start_date: date,
    included_account_ids: list[str] | None = None,
    excluded_account_ids: list[str] | None = None,
) -> list[dict[str, object]]:
    """Return daily inflow/outflow aggregates for the lookback window."""
    included_ids = included_account_ids or []
    excluded_ids = excluded_account_ids or []

    lookback_start = start_date - timedelta(days=LOOKBACK_DAYS)
    date_expr = func.date(Transaction.date).label("date")
    inflow_sum = func.sum(
        case((Transaction.amount > 0, Transaction.amount), else_=0)
    ).label("inflow")
    outflow_sum = func.sum(
        case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)
    ).label("outflow")

    query = (
        db.session.query(date_expr, inflow_sum, outflow_sum)
        .join(Account, Transaction.account_id == Account.account_id)
        .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
        .filter(
            (Transaction.is_internal.is_(False)) | (Transaction.is_internal.is_(None))
        )
        .filter(Transaction.date >= lookback_start)
        .filter(Transaction.date <= start_date)
    )
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if included_ids:
        query = query.filter(Transaction.account_id.in_(included_ids))
    if excluded_ids:
        query = query.filter(~Transaction.account_id.in_(excluded_ids))

    rows = query.group_by(date_expr).order_by(date_expr).all()
    return [
        {
            "date": row.date,
            "inflow": float(row.inflow or 0),
            "outflow": float(row.outflow or 0),
        }
        for row in rows
    ]


def _build_realized_history(
    *,
    start_date: date,
    ending_balance: float,
    historical_aggregates: list[dict[str, object]],
    lookback_days: int,
) -> list[dict[str, object]]:
    """Reverse-map daily EOD balances for the chart's realized history.

    The ``ending_balance`` represents the known balance on ``start_date``.
    We walk backward day-by-day subtracting each day's net activity to recover
    prior end-of-day balances.
    """
    bounded_lookback = max(int(lookback_days or 1), 1)
    lookback_start = start_date - timedelta(days=bounded_lookback - 1)

    daily_net_by_date: dict[date, float] = {}
    for aggregate in historical_aggregates:
        raw_date = aggregate.get("date")
        if raw_date is None:
            continue

        if isinstance(raw_date, datetime):
            aggregate_date = raw_date.date()
        elif isinstance(raw_date, date):
            aggregate_date = raw_date
        else:
            aggregate_date = datetime.fromisoformat(str(raw_date)).date()

        inflow = float(
            aggregate.get("inflow")
            or aggregate.get("income")
            or aggregate.get("credit")
            or 0
        )
        outflow = float(
            aggregate.get("outflow")
            or aggregate.get("expense")
            or aggregate.get("debit")
            or 0
        )
        daily_net_by_date[aggregate_date] = (
            daily_net_by_date.get(aggregate_date, 0.0) + inflow - outflow
        )

    realized_history_desc: list[dict[str, object]] = []
    running_balance = float(ending_balance or 0)
    current_date = start_date
    while current_date >= lookback_start:
        iso_date = current_date.isoformat()
        realized_history_desc.append(
            {
                "date": iso_date,
                "label": iso_date,
                "balance": round(running_balance, 2),
            }
        )
        running_balance -= daily_net_by_date.get(current_date, 0.0)
        current_date -= timedelta(days=1)

    realized_history_desc.reverse()
    return realized_history_desc


@forecast.route("", methods=["GET"])
def get_forecast():
    """Return forecast payload generated by :class:`ForecastOrchestrator`."""
    try:
        view_type = request.args.get("view_type", "Month")  # noqa: F841
        manual_income = float(request.args.get("manual_income", 0))
        liability_rate = float(request.args.get("liability_rate", 0))

        orchestrator = ForecastOrchestrator(db.session)
        payload = orchestrator.build_forecast_payload(
            user_id=request.args.get("user_id"),
            view_type=view_type,
            manual_income=manual_income,
            liability_rate=liability_rate,
        )
        return jsonify(payload), 200
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Error generating forecast payload: %s", e, exc_info=True)
        return jsonify({"error": "Unable to load forecast data."}), 500


@forecast.route("/compute", methods=["POST"])
def compute_forecast_route():
    """Compute a forecast result for the requested horizon and adjustments."""
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id") or request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required."}), 400

    try:
        start_date = _parse_start_date(payload.get("start_date"))
        horizon_days = _parse_horizon_days(payload.get("horizon_days"))
        moving_average_window = _parse_moving_average_window(
            payload.get("moving_average_window")
        )
        normalize = _parse_normalize(payload.get("normalize"))
        graph_mode = _parse_graph_mode(payload.get("graph_mode"))
        included_account_ids, excluded_account_ids = _parse_account_filters(payload)
    except ValueError as exc:
        logger.warning("Invalid forecast compute request: %s", exc)
        return jsonify({"error": str(exc)}), 400

    adjustments = payload.get("adjustments", [])
    if adjustments is None:
        adjustments = []
    if not isinstance(adjustments, list):
        return jsonify({"error": "adjustments must be a list."}), 400

    try:
        latest_snapshots = _load_latest_snapshots(
            str(user_id),
            included_account_ids=included_account_ids,
            excluded_account_ids=excluded_account_ids,
        )
        historical_aggregates = _load_historical_aggregates(
            str(user_id),
            start_date,
            included_account_ids=included_account_ids,
            excluded_account_ids=excluded_account_ids,
        )

        net_snapshot_balance = sum(
            float(snapshot.get("balance", 0) or 0) for snapshot in latest_snapshots
        )
        total_inflow = sum(
            float(item.get("inflow", 0) or 0) for item in historical_aggregates
        )
        total_outflow = sum(
            float(item.get("outflow", 0) or 0) for item in historical_aggregates
        )
        realized_history = _build_realized_history(
            start_date=start_date,
            ending_balance=net_snapshot_balance,
            historical_aggregates=historical_aggregates,
            lookback_days=LOOKBACK_DAYS,
        )
        result = compute_forecast(
            user_id=str(user_id),
            start_date=start_date,
            horizon_days=horizon_days,
            latest_snapshots=latest_snapshots,
            historical_aggregates=historical_aggregates,
            adjustments=adjustments,
            moving_average_window=moving_average_window,
            normalize=normalize,
            graph_mode=graph_mode,
            metadata={
                "lookback_days": LOOKBACK_DAYS,
                "included_account_ids": included_account_ids,
                "excluded_account_ids": excluded_account_ids,
                "starting_balance": net_snapshot_balance,
                "contribution_totals": {
                    "snapshot_balance": net_snapshot_balance,
                    "historical_inflow": total_inflow,
                    "historical_outflow": total_outflow,
                },
                "realized_history_lookback_days": LOOKBACK_DAYS,
                "realized_history": realized_history,
            },
        )
        return jsonify(result), 200
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Forecast compute failed: %s", exc, exc_info=True)
        return jsonify({"error": "Unable to compute forecast."}), 500
