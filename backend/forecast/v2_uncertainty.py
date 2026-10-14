"""Forecast V2 uncertainty: seeded Monte Carlo bands and shortfall risk.

Every simulated path starts from the same liquid cash and the same known contractual events as the
deterministic baseline (``v2_core.simulate_cash_ledger``). Only evidence-backed uncertainty varies:

* **Residual spending/income** is block-bootstrapped by calendar week from the user's own de-recurred
  history, so within-week correlation is kept and no value exceeds what was observed.
* **Inferred recurring streams** get one date shift (-1/0/+1 day, odds from the heuristic detection
  confidence) and one amount factor (within the stream's observed dispersion) *per path*, shared by
  every instance of the stream, so the variation is correlated rather than fresh noise each month.
* Manual rules, saved recurring rules and adjustments are fixed.

If the history cannot support a variance estimate the result says so (``uncertainty_available`` is
False) and carries no percentile bands. Percentiles are model output, not guarantees, and are not the
heuristic detection confidence of a stream.

Randomness is a local ``random.Random(seed)``; no process-global state is touched.
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import ForecastUncertaintyResult, ForecastV2Event
from .v2_core import ForecastV2InputError, _to_date, simulate_cash_ledger

MODEL_VERSION = "v2"
MAX_SIMULATIONS = 1000
DEFAULT_SIMULATIONS = 500
MAX_HORIZON_DAYS = 365
MIN_HISTORY_WEEKS = 4
NOMINAL_INTERVAL = 0.8  # P10-P90


def _cents(value: Any) -> int:
    return int((Decimal(str(value)) * 100).to_integral_value())


def estimate_residual_uncertainty(
    residual_history: Iterable[Mapping[str, Any]], *, min_weeks: int = MIN_HISTORY_WEEKS
) -> dict[str, Any]:
    """Summarize clean residual history as complete calendar weeks for bootstrapping.

    Args:
        residual_history: Contiguous daily rows ``{"date", "spend", "income"}`` (zeros included),
            as returned by ``v2_sources.build_v2_inputs()["residual_history"]``.
        min_weeks: Minimum complete Monday-Sunday weeks required.

    Returns:
        ``{"available", "reason", "history_days", "week_count", "weeks", "weekly_net_mean",
        "weekly_net_stdev"}`` where ``weeks`` are 7-item lists of net cents (Mon..Sun). When
        ``available`` is False no variance is reported.
    """
    net: dict[date, int] = {}
    for row in residual_history:
        net[_to_date(row["date"], field_name="residual date")] = _cents(row.get("spend", 0)) + _cents(
            row.get("income", 0)
        )
    history_days = len(net)
    weeks: list[list[int]] = []
    for day in sorted(net):
        if day.weekday() != 0:
            continue
        week = [day + timedelta(days=i) for i in range(7)]
        if all(d in net for d in week):
            weeks.append([net[d] for d in week])
    summary: dict[str, Any] = {
        "available": len(weeks) >= min_weeks,
        "reason": None,
        "history_days": history_days,
        "week_count": len(weeks),
        "weeks": weeks,
        "weekly_net_mean": None,
        "weekly_net_stdev": None,
    }
    if not summary["available"]:
        summary["reason"] = f"insufficient_history: {len(weeks)} complete weeks, need {min_weeks}"
        summary["weeks"] = []
        return summary
    totals = [sum(w) for w in weeks]
    mean = sum(totals) / len(totals)
    summary["weekly_net_mean"] = round(mean / 100, 2)
    summary["weekly_net_stdev"] = round(math.sqrt(sum((t - mean) ** 2 for t in totals) / len(totals)) / 100, 2)
    return summary


def _validate(
    *, horizon_days: Any, simulation_count: Any, threshold: Any, seed: Any, account_snapshots: Sequence[Any]
) -> Decimal:
    if not isinstance(horizon_days, int) or isinstance(horizon_days, bool) or not 1 <= horizon_days <= MAX_HORIZON_DAYS:
        raise ForecastV2InputError("invalid_horizon", f"horizon_days must be 1..{MAX_HORIZON_DAYS}")
    if (
        not isinstance(simulation_count, int)
        or isinstance(simulation_count, bool)
        or not 1 <= simulation_count <= MAX_SIMULATIONS
    ):
        raise ForecastV2InputError("invalid_simulation_count", f"simulation_count must be 1..{MAX_SIMULATIONS}")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ForecastV2InputError("invalid_seed", "seed must be an integer")
    try:
        limit = Decimal(str(threshold))
    except (InvalidOperation, ValueError) as exc:
        raise ForecastV2InputError("invalid_threshold", f"threshold is not numeric: {threshold!r}") from exc
    if isinstance(threshold, bool) or not limit.is_finite() or limit < 0:
        raise ForecastV2InputError("invalid_threshold", "threshold must be a finite, non-negative amount")
    if not account_snapshots:
        raise ForecastV2InputError("empty_account_scope", "account_snapshots is empty; nothing to simulate")
    return limit


def _percentile(sorted_values: Sequence[int], q: float) -> int:
    position = q * (len(sorted_values) - 1)
    low, high = math.floor(position), math.ceil(position)
    return int(round(sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)))


def simulate_v2_paths(
    *,
    start_date: date | str,
    horizon_days: int,
    account_snapshots: Iterable[Any],
    scheduled_events: Iterable[ForecastV2Event] = (),
    residual_events: Iterable[ForecastV2Event] = (),
    residual_history: Iterable[Mapping[str, Any]] = (),
    simulation_count: int = DEFAULT_SIMULATIONS,
    seed: int,
    threshold: Any = 0,
    owner_id: Any = None,
) -> ForecastUncertaintyResult:
    """Simulate seeded cash paths and summarize P10/P50/P90 plus shortfall probabilities.

    Args:
        start_date: First projected day.
        horizon_days: 1..365.
        account_snapshots: Authorized accounts (see ``simulate_cash_ledger``); must be non-empty.
        scheduled_events: ``v2_sources`` scheduled events. Events with ``source == "inferred"``
            are uncertain (shared per-stream date shift and amount factor); the rest are fixed.
        residual_events: Deterministic residual means; used for the baseline only.
        residual_history: Daily residual rows for the weekly block bootstrap.
        simulation_count: 1..1000 (default 500).
        seed: Integer seed for a call-local RNG.
        threshold: Non-negative cash floor for ``probability_cash_below_threshold_any_day``.
        owner_id: Forwarded to the ledger's ownership filter.

    Returns:
        ``ForecastUncertaintyResult``. ``risk`` probabilities are computed from each path's
        minimum balance over the whole horizon, not the ending balance.

    Raises:
        ForecastV2InputError: invalid horizon/count/seed/threshold, or an empty account scope.
    """
    accounts = list(account_snapshots)
    limit = _validate(
        horizon_days=horizon_days,
        simulation_count=simulation_count,
        threshold=threshold,
        seed=seed,
        account_snapshots=accounts,
    )
    start = _to_date(start_date, field_name="start_date")
    scheduled = list(scheduled_events)
    base_events = scheduled + list(residual_events)
    baseline = simulate_cash_ledger(
        start_date=start, horizon_days=horizon_days, account_snapshots=accounts, events=base_events, owner_id=owner_id
    )
    common = dict(
        model_version=MODEL_VERSION,
        seed=seed,
        simulation_count=simulation_count,
        horizon_days=horizon_days,
        threshold=float(limit),
    )
    if baseline.status != "ok":
        return ForecastUncertaintyResult(
            uncertainty_available=False,
            reason="no_liquid_cash_accounts",
            history_coverage_days=0,
            warnings=baseline.warnings,
            **common,
        )
    baseline_rows = [{"date": p.date.isoformat(), "baseline": float(p.ending_cash)} for p in baseline.daily]
    estimate = estimate_residual_uncertainty(residual_history)
    if not estimate["available"]:
        return ForecastUncertaintyResult(
            uncertainty_available=False,
            reason=estimate["reason"],
            history_coverage_days=estimate["history_days"],
            baseline=baseline_rows,
            bands=[],
            assumptions={"method": "weekly_block_bootstrap", "history_weeks": estimate["week_count"]},
            warnings=baseline.warnings,
            **common,
        )

    applied = {e.event_id for e in baseline.events}
    uncertain = sorted(
        (
            e
            for e in scheduled
            if e.source == "inferred" and e.event_id in applied and e.kind in {"scheduled_income", "scheduled_bill"}
        ),
        key=lambda e: (str(e.source_id), e.date, e.event_id),
    )
    uncertain_ids = {e.event_id for e in uncertain}
    fixed = [e for e in scheduled if e.event_id not in uncertain_ids]
    fixed_ledger = simulate_cash_ledger(
        start_date=start, horizon_days=horizon_days, account_snapshots=accounts, events=fixed, owner_id=owner_id
    )
    fixed_cash = [_cents(p.ending_cash) for p in fixed_ledger.daily]
    days = [start + timedelta(days=i) for i in range(horizon_days)]
    streams: dict[str, list[ForecastV2Event]] = {}
    for event in uncertain:
        streams.setdefault(str(event.source_id), []).append(event)

    rng = random.Random(seed)
    weeks = estimate["weeks"]
    first_monday = start - timedelta(days=start.weekday())
    block_of_day = [(d - first_monday).days // 7 for d in days]
    block_count = block_of_day[-1] + 1
    columns: list[list[int]] = [[] for _ in range(horizon_days)]
    minima: list[int] = []

    for _ in range(simulation_count):
        delta = [0] * horizon_days
        for stream_id in sorted(streams):
            group = streams[stream_id]
            confidence = group[0].confidence if group[0].confidence is not None else 0.5
            shift_odds = min(0.5, max(0.0, 1.0 - confidence))
            draw = rng.random()
            shift = -1 if draw < shift_odds / 2 else 1 if draw < shift_odds else 0
            dispersion = float(group[0].metadata.get("amount_dispersion") or 0.0)
            factor = 1.0 + (rng.random() * 2 - 1) * dispersion if dispersion > 0 else 1.0
            for event in group:
                index = (event.date - start).days + shift
                if 0 <= index < horizon_days:
                    delta[index] += int(round(_cents(event.amount) * factor))
        chosen = [rng.randrange(len(weeks)) for _ in range(block_count)]
        for i, day in enumerate(days):
            delta[i] += weeks[chosen[block_of_day[i]]][day.weekday()]
        running, lowest = 0, None
        for i in range(horizon_days):
            running += delta[i]
            balance = fixed_cash[i] + running
            columns[i].append(balance)
            lowest = balance if lowest is None or balance < lowest else lowest
        minima.append(lowest)

    bands = []
    for i, day in enumerate(days):
        ordered = sorted(columns[i])
        bands.append(
            {
                "date": day.isoformat(),
                "p10": _percentile(ordered, 0.10) / 100,
                "p50": _percentile(ordered, 0.50) / 100,
                "p90": _percentile(ordered, 0.90) / 100,
                "baseline": baseline_rows[i]["baseline"],
            }
        )
    limit_cents = _cents(limit)
    risk = {
        "probability_cash_below_zero_any_day": sum(m < 0 for m in minima) / simulation_count,
        "probability_cash_below_threshold_any_day": sum(m < limit_cents for m in minima) / simulation_count,
        "threshold": float(limit),
        "simulation_count": simulation_count,
        "seed": seed,
        "model_version": MODEL_VERSION,
        "history_coverage_days": estimate["history_days"],
    }
    return ForecastUncertaintyResult(
        uncertainty_available=True,
        reason=None,
        history_coverage_days=estimate["history_days"],
        baseline=baseline_rows,
        bands=bands,
        risk=risk,
        assumptions={
            "method": "weekly_block_bootstrap",
            "history_weeks": estimate["week_count"],
            "weekly_net_mean": estimate["weekly_net_mean"],
            "weekly_net_stdev": estimate["weekly_net_stdev"],
            "uncertain_streams": sorted(streams),
            "fixed_event_count": len(fixed),
            "uncertain_event_count": len(uncertain),
            "date_jitter_days": 1,
            "interval": {"lower": "p10", "upper": "p90", "nominal_coverage": NOMINAL_INTERVAL},
            "note": "Percentiles are simulation output from limited history, not guarantees.",
        },
        warnings=baseline.warnings,
        **common,
    )
