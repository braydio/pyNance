"""Forecast projection helpers for balance timelines."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import DateLike, ForecastTimelinePoint


def _parse_date(value: DateLike | None, fallback: date) -> date:
    """Return a date instance from a date-like value."""
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(value).date()


def _to_decimal(value: Any) -> Decimal:
    """Coerce numeric values into a Decimal, defaulting to zero on bad input."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _extract_amount(entry: Mapping[str, Any], keys: Iterable[str]) -> Decimal:
    """Pull the first available numeric amount from a mapping."""
    for key in keys:
        if key in entry and entry[key] is not None:
            return _to_decimal(entry[key])
    return Decimal("0")


def project_balances(
    user_id: int,
    start_date: DateLike,
    horizon_days: int,
    latest_snapshots: Sequence[Mapping[str, Any]],
    historical_aggregates: Sequence[Mapping[str, Any]],
) -> list[ForecastTimelinePoint]:
    """Project a daily balance timeline using average inflows/outflows.

    Args:
        user_id: Identifier for the user owning the balances.
        start_date: First date included in the projection.
        horizon_days: Number of days to project, including the start date.
        latest_snapshots: Latest balance snapshots for the user. Each mapping should include a
            ``balance`` field and ideally an ``account_id`` and ``date`` for deterministic
            selection.
        historical_aggregates: Historical daily aggregates with inflow/outflow totals. Each mapping
            should include a ``date`` plus inflow/outflow fields such as ``inflow``/``outflow`` or
            ``income``/``expense``.

    Returns:
        A list of :class:`ForecastTimelinePoint` entries ordered by date.
    """

    anchor_date = _parse_date(start_date, fallback=date.today())
    horizon_days = max(int(horizon_days), 0)

    # Select the latest snapshot per account for the requested user to anchor the forecast.
    latest_by_account: dict[str, tuple[date, Decimal]] = {}
    for index, snapshot in enumerate(latest_snapshots):
        snapshot_user = snapshot.get("user_id")
        if snapshot_user is not None and snapshot_user != user_id:
            continue

        account_id = str(snapshot.get("account_id", snapshot.get("id", index)))
        snapshot_date = _parse_date(
            snapshot.get("date") or snapshot.get("as_of"),
            fallback=anchor_date,
        )
        balance = _to_decimal(snapshot.get("balance"))

        existing = latest_by_account.get(account_id)
        if existing is None:
            latest_by_account[account_id] = (snapshot_date, balance)
            continue

        existing_date, existing_balance = existing
        if snapshot_date > existing_date or (
            snapshot_date == existing_date and balance > existing_balance
        ):
            latest_by_account[account_id] = (snapshot_date, balance)

    starting_balance = sum(
        (balance for _, balance in latest_by_account.values()), Decimal("0")
    )

    # Compute the average inflow/outflow per day from historical aggregates.
    inflow_keys = (
        "inflow",
        "inflows",
        "income",
        "credit",
        "total_inflow",
        "inflow_total",
    )
    outflow_keys = (
        "outflow",
        "outflows",
        "expense",
        "debit",
        "total_outflow",
        "outflow_total",
    )
    net_keys = ("net", "net_change", "net_total")

    total_inflow = Decimal("0")
    total_outflow = Decimal("0")
    aggregate_dates: set[date] = set()

    for aggregate in historical_aggregates:
        aggregate_date = aggregate.get("date")
        if aggregate_date is not None:
            aggregate_dates.add(_parse_date(aggregate_date, fallback=anchor_date))

        inflow = _extract_amount(aggregate, inflow_keys)
        outflow = _extract_amount(aggregate, outflow_keys)

        if inflow == Decimal("0") and outflow == Decimal("0"):
            net_amount = _extract_amount(aggregate, net_keys)
            if net_amount > 0:
                inflow = net_amount
            elif net_amount < 0:
                outflow = abs(net_amount)

        total_inflow += inflow
        total_outflow += outflow

    day_count = len(aggregate_dates) if aggregate_dates else len(historical_aggregates)
    if day_count <= 0:
        average_inflow = Decimal("0")
        average_outflow = Decimal("0")
    else:
        average_inflow = total_inflow / Decimal(day_count)
        average_outflow = total_outflow / Decimal(day_count)

    # Build the projection by applying the average daily net change to the latest balance.
    points: list[ForecastTimelinePoint] = []
    current_balance = starting_balance
    for day_offset in range(horizon_days):
        current_date = anchor_date + timedelta(days=day_offset)

        # Apply the daily net change before recording the day's projected balance.
        current_balance += average_inflow - average_outflow

        points.append(
            ForecastTimelinePoint(
                date=current_date,
                label=current_date.isoformat(),
                forecast_balance=float(current_balance),
                metadata={
                    "average_inflow": float(average_inflow),
                    "average_outflow": float(average_outflow),
                    "starting_balance": float(starting_balance),
                },
            )
        )

    return points
