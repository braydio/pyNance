"""Forecast V2 validation: leakage-safe rolling as-of backtests.

``backtest_v2`` replays the V2 forecast at each cutoff using only data dated on or before that
cutoff, then scores it against realized liquid cash. It is pure: all data access goes through the
loader callables, and ``history_loaders`` builds them from in-memory history with as-of slicing.

Scoring rules:
    * Balance error is ``predicted - actual`` on the end-of-day liquid cash total, so a positive
      bias means over-forecasting. Missing truth is skipped and counted, never treated as zero.
    * Recurring checks compare the first projected occurrence of each promoted stream with the
      nearest realized transaction of the same stream (account, merchant, sign) inside the window.
      Streams whose predicted date is beyond the observed data are ``unobserved``; misses are counted.
    * Negative-cash precision/recall are reported only when the evaluated folds contain both outcomes.
    * P10-P90 coverage is only computed when ``with_uncertainty`` is set and bands exist.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from .models import ForecastBacktestReport
from .v2_core import (
    BUCKET_CASH,
    ForecastV2InputError,
    _read,
    _to_date,
    _to_decimal,
    classify_forecast_account,
    simulate_cash_ledger,
)
from .v2_sources import build_v2_inputs, normalize_merchant_key
from .v2_uncertainty import MODEL_VERSION, NOMINAL_INTERVAL, simulate_v2_paths

DEFAULT_HORIZONS = (7, 14, 30)
MAX_FOLDS = 120


def history_loaders(
    *,
    accounts: Iterable[Any],
    transactions: Iterable[Any],
    snapshots: Iterable[Any],
    recurring_rules: Iterable[Any] = (),
    manual_rules: Iterable[Any] = (),
) -> tuple[Callable, Callable, Callable]:
    """Build ``(load_inputs, load_truth, load_realized)`` over in-memory history.

    ``snapshots`` are ``{account_id, date, balance}``. ``load_inputs(cutoff)`` returns accounts whose
    balance is the latest snapshot **on or before** the cutoff plus the same transactions (the
    forecast pipeline itself drops anything after the cutoff). ``load_truth(day)`` is the cash total on
    exactly that day, or ``None`` unless every cash account has a snapshot that day.
    """
    account_list = [dict(a) if isinstance(a, Mapping) else dict(vars(a)) for a in accounts]
    tx_list = list(transactions)
    snaps: dict[str, dict[date, Decimal]] = {}
    for snap in snapshots:
        snaps.setdefault(str(_read(snap, "account_id")), {})[_to_date(_read(snap, "date"))] = _to_decimal(
            _read(snap, "balance")
        )
    cash_ids = [str(a["account_id"]) for a in account_list if classify_forecast_account(a) == BUCKET_CASH]

    def load_inputs(cutoff: date) -> dict[str, Any]:
        sliced = []
        for account in account_list:
            history = snaps.get(str(account["account_id"]), {})
            usable = [d for d in history if d <= cutoff]
            latest = max(usable) if usable else None
            sliced.append({**account, "balance": history[latest] if latest else None, "as_of": latest})
        return {
            "accounts": sliced,
            "transactions": tx_list,
            "recurring_rules": list(recurring_rules),
            "manual_rules": list(manual_rules),
        }

    def load_truth(day: date) -> Optional[Decimal]:
        if not cash_ids or any(day not in snaps.get(i, {}) for i in cash_ids):
            return None
        return sum((snaps[i][day] for i in cash_ids), Decimal("0.00"))

    def load_realized(cutoff: date, end: date) -> dict[str, Any]:
        rows = [t for t in tx_list if cutoff < _to_date(_read(t, "date")) <= end]
        known = [d for ids in snaps.values() for d in ids] + [_to_date(_read(t, "date")) for t in tx_list]
        return {"transactions": rows, "through": max(known) if known else cutoff}

    return load_inputs, load_truth, load_realized


def _mean(values: Sequence[float]) -> Optional[float]:
    return round(sum(values) / len(values), 4) if values else None


def _match_realized(event: Any, merchant_key: str, realized: Sequence[Any], window_days: int) -> Optional[Any]:
    """Nearest realized transaction of the same stream within ``window_days`` of the prediction."""
    best = None
    for tx in realized:
        amount = _to_decimal(_read(tx, "amount"))
        if (1 if amount > 0 else -1) != (1 if event.amount > 0 else -1):
            continue
        if (
            _read(tx, "account_id") is not None
            and event.account_id
            and str(_read(tx, "account_id")) != event.account_id
        ):
            continue
        if normalize_merchant_key(tx) != merchant_key:
            continue
        gap = abs((_to_date(_read(tx, "date")) - event.date).days)
        if gap <= window_days and (best is None or gap < best[0]):
            best = (gap, tx)
    return best[1] if best else None


def backtest_v2(
    *,
    cutoffs: Iterable[date | str],
    load_inputs: Callable[[date], Mapping[str, Any]],
    load_truth: Callable[[date], Optional[Decimal]],
    load_realized: Optional[Callable[[date, date], Mapping[str, Any]]] = None,
    horizons: Sequence[int] = DEFAULT_HORIZONS,
    max_anchor_age_days: int = 1,
    recurring_match_days: int = 5,
    with_uncertainty: bool = False,
    simulation_count: int = 200,
    seed: int = 12345,
    options: Optional[Mapping[str, Any]] = None,
) -> ForecastBacktestReport:
    """Replay the V2 forecast at each cutoff and score it.

    Args:
        cutoffs: As-of dates (``<= MAX_FOLDS`` of them). The forecast starts the next day.
        load_inputs: ``cutoff -> {"accounts", "transactions", "recurring_rules", "manual_rules"}``
            with account balances as of that cutoff (``history_loaders`` provides one).
        load_truth: ``day -> total eligible cash balance`` or ``None`` when unknown.
        load_realized: ``(cutoff, end) -> {"transactions", "through"}`` for recurring-event checks.
        horizons: Horizons to score; defaults to 7, 14 and 30 days.
        max_anchor_age_days: A fold is skipped when the cutoff balance snapshot is older than this.
        recurring_match_days: Allowed date distance when matching a realized occurrence.
        with_uncertainty: Also simulate P10/P90 and score empirical coverage.
        simulation_count: Paths per fold when ``with_uncertainty`` is set.
        seed: Seed for the uncertainty simulations.
        options: Overrides for ``v2_sources.DEFAULT_OPTIONS``.

    Returns:
        ``ForecastBacktestReport``.

    Raises:
        ForecastV2InputError: no cutoffs, too many cutoffs or invalid horizons.
    """
    cutoff_list = sorted({_to_date(c, field_name="cutoff") for c in cutoffs})
    horizon_list = sorted({int(h) for h in horizons})
    if not cutoff_list:
        raise ForecastV2InputError("no_cutoffs", "at least one cutoff is required")
    if len(cutoff_list) > MAX_FOLDS:
        raise ForecastV2InputError("too_many_cutoffs", f"at most {MAX_FOLDS} cutoffs per backtest")
    if not horizon_list or horizon_list[0] < 1 or horizon_list[-1] > 365:
        raise ForecastV2InputError("invalid_horizon", "horizons must be within 1..365")
    longest = horizon_list[-1]

    skipped: Counter[str] = Counter()
    folds: list[dict[str, Any]] = []
    errors: dict[int, list[float]] = {h: [] for h in horizon_list}
    coverage_hits: dict[int, list[bool]] = {h: [] for h in horizon_list}
    date_errors: list[float] = []
    amount_errors: list[float] = []
    recurring = Counter()
    neg_outcomes: list[tuple[bool, bool]] = []

    for cutoff in cutoff_list:
        data = load_inputs(cutoff)
        accounts = list(data["accounts"])
        cash = [a for a in accounts if classify_forecast_account(a) == BUCKET_CASH]
        anchors = [_read(a, "as_of") for a in cash]
        if not cash or any(_read(a, "balance") is None or d is None for a, d in zip(cash, anchors)):
            skipped["no_anchor_snapshot"] += 1
            folds.append({"cutoff": cutoff.isoformat(), "status": "skipped", "reason": "no_anchor_snapshot"})
            continue
        if any((cutoff - _to_date(d)).days > max_anchor_age_days for d in anchors):
            skipped["stale_anchor"] += 1
            folds.append({"cutoff": cutoff.isoformat(), "status": "skipped", "reason": "stale_anchor"})
            continue
        start = cutoff + timedelta(days=1)
        inputs = build_v2_inputs(
            transactions=data["transactions"],
            recurring_rules=data.get("recurring_rules", ()),
            manual_rules=data.get("manual_rules", ()),
            accounts=accounts,
            as_of_date=cutoff,
            start_date=start,
            horizon_days=longest,
            options=options,
        )
        events = inputs["scheduled_events"] + inputs["residual_events"]
        ledger = simulate_cash_ledger(start_date=start, horizon_days=longest, account_snapshots=accounts, events=events)
        if ledger.status != "ok":
            skipped["insufficient_data"] += 1
            folds.append({"cutoff": cutoff.isoformat(), "status": "skipped", "reason": "insufficient_data"})
            continue

        bands: dict[str, Mapping[str, Any]] = {}
        if with_uncertainty:
            result = simulate_v2_paths(
                start_date=start,
                horizon_days=longest,
                account_snapshots=accounts,
                scheduled_events=inputs["scheduled_events"],
                residual_events=inputs["residual_events"],
                residual_history=inputs["residual_history"],
                simulation_count=simulation_count,
                seed=seed,
            )
            bands = {b["date"]: b for b in result.bands}

        truth_by_day = {}
        for offset in range(1, longest + 1):
            truth_by_day[offset] = load_truth(cutoff + timedelta(days=offset))
        predictions: dict[str, Any] = {}
        evaluated_any = False
        for horizon in horizon_list:
            predicted = ledger.daily[horizon - 1].ending_cash
            actual = truth_by_day[horizon]
            row: dict[str, Any] = {"predicted": float(predicted), "actual": None if actual is None else float(actual)}
            if actual is None:
                skipped["missing_truth_horizons"] += 1
            else:
                evaluated_any = True
                error = float(predicted - actual)
                row["error"] = error
                errors[horizon].append(error)
                band = bands.get(ledger.daily[horizon - 1].date.isoformat())
                if band:
                    row["p10"], row["p90"] = band["p10"], band["p90"]
                    coverage_hits[horizon].append(band["p10"] <= float(actual) <= band["p90"])
            predictions[str(horizon)] = row

        # Negative-cash classification over the longest window (needs truth for every day).
        window_truth = [truth_by_day[o] for o in range(1, longest + 1)]
        if all(t is not None for t in window_truth):
            neg_outcomes.append(
                (
                    any(p.ending_cash < 0 for p in ledger.daily[:longest]),
                    any(t < 0 for t in window_truth),
                )
            )

        # Recurring next-occurrence checks.
        if load_realized is not None:
            realized = load_realized(cutoff, cutoff + timedelta(days=longest))
            through = _to_date(realized["through"])
            first_seen: dict[str, Any] = {}
            for event in inputs["scheduled_events"]:
                first_seen.setdefault(str(event.source_id), event)
            stream_keys = {s["stream_id"]: s for s in inputs["streams"]}
            for stream_id, event in sorted(first_seen.items()):
                meta = stream_keys.get(stream_id)
                if meta is None or meta["origin"] == "manual" or not meta.get("merchant_key"):
                    continue
                if event.date > through:
                    recurring["unobserved"] += 1
                    continue
                match = _match_realized(event, meta["merchant_key"], realized["transactions"], recurring_match_days)
                if match is None:
                    recurring["missed"] += 1
                    continue
                recurring["matched"] += 1
                date_errors.append(float((event.date - _to_date(_read(match, "date"))).days))
                amount_errors.append(float(abs(event.amount - _to_decimal(_read(match, "amount")))))

        status = "evaluated" if evaluated_any else "skipped"
        if not evaluated_any:
            skipped["no_truth_in_window"] += 1
        folds.append(
            {
                "cutoff": cutoff.isoformat(),
                "status": status,
                "reason": None if evaluated_any else "no_truth_in_window",
                "predictions": predictions,
                "scheduled_event_count": len(inputs["scheduled_events"]),
                "history_days": inputs["coverage"]["history_days"],
                "coverage_confidence": inputs["coverage"]["confidence"],
            }
        )

    positives = [o for o in neg_outcomes if o[1]]
    negatives = [o for o in neg_outcomes if not o[1]]
    tp = sum(1 for p, a in neg_outcomes if p and a)
    fp = sum(1 for p, a in neg_outcomes if p and not a)
    fn = sum(1 for p, a in neg_outcomes if not p and a)
    supported = bool(positives) and bool(negatives)
    negative_cash = {
        "supported": supported,
        "evaluated_folds": len(neg_outcomes),
        "precision": (tp / (tp + fp) if tp + fp else None) if supported else None,
        "recall": (tp / (tp + fn) if tp + fn else None) if supported else None,
        "reason": None if supported else "needs folds with and without actual negative cash",
    }
    evaluated = [f for f in folds if f["status"] == "evaluated"]
    first = cutoff_list[0].isoformat()
    last = cutoff_list[-1].isoformat()
    return ForecastBacktestReport(
        model_version=MODEL_VERSION,
        horizons=horizon_list,
        cutoffs_requested=len(cutoff_list),
        folds_evaluated=len(evaluated),
        skipped=dict(sorted(skipped.items())),
        balance={
            str(h): {
                "samples": len(errors[h]),
                "mae": _mean([abs(e) for e in errors[h]]),
                "bias": _mean(errors[h]),
            }
            for h in horizon_list
        },
        recurring={
            "matched": recurring["matched"],
            "missed": recurring["missed"],
            "unobserved": recurring["unobserved"],
            "date_error_mae_days": _mean([abs(e) for e in date_errors]),
            "date_error_bias_days": _mean(date_errors),
            "amount_error_mae": _mean(amount_errors),
        },
        negative_cash=negative_cash,
        interval_coverage=(
            {
                str(h): {
                    "samples": len(coverage_hits[h]),
                    "coverage": _mean([1.0 if hit else 0.0 for hit in coverage_hits[h]]),
                    "nominal": NOMINAL_INTERVAL,
                }
                for h in horizon_list
            }
            if with_uncertainty
            else {}
        ),
        folds=folds,
        data_window={
            "first_cutoff": first,
            "last_cutoff": last,
            "evaluated_history_days": [f["history_days"] for f in evaluated],
        },
    )
