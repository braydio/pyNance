"""Forecast V2 orchestration for ``POST /api/forecast/compute`` with ``model_version: "v2"``.

Loads one user's as-of data (``forecast_v2_sources``), builds the deterministic liquid-cash ledger,
optionally seeded P10/P50/P90 bands, and replays request-local what-if scenarios through the same
engine. Nothing is written to the database and scenarios are never persisted.

Access model: this deployment identifies the caller by the request body's ``user_id`` (there is no
session authentication on the forecast routes). V2 therefore fails closed: account ids that are not
owned by that user raise ``ForecastV2AccessError`` (HTTP 403) instead of being silently ignored, and every
query is scoped to ``user_id``. Do not treat ``user_id`` as proof of identity if real authentication is
added; plug the authenticated id in at the route.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Iterable, Optional

from forecast.models import ForecastV2Event
from forecast.v2_core import CENT, ForecastV2InputError, simulate_cash_ledger
from forecast.v2_sources import build_v2_inputs
from forecast.v2_uncertainty import DEFAULT_SIMULATIONS, MAX_SIMULATIONS, simulate_v2_paths

from app.models import Account
from app.services.forecast_v2_sources import load_v2_source_data

MODEL_VERSION = "v2"
MAX_HORIZON_DAYS = 365
MAX_SCENARIOS = 5
MAX_ADJUSTMENTS = 100
MAX_DRIVERS = 100
DEFAULT_SEED = 12345
SCENARIO_KEYS = {"residual_spending_multiplier", "income_multiplier", "delay_income_days", "adjustments"}
_ORIGIN_LABELS = {
    "manual": "manual_rule",
    "recurring_rule": "confirmed_recurring",
    "inferred_confirmed": "confirmed_recurring",
    "inferred": "detected_recurring",
}


class ForecastV2RequestError(ValueError):
    """Invalid V2 request (HTTP 400)."""


class ForecastV2AccessError(PermissionError):
    """Requested accounts are not available to this user (HTTP 403)."""


# --------------------------------------------------------------------------- parsing


def _number(value: Any, name: str, *, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ForecastV2RequestError(f"{name} must be a number.")
    if value != value or value in (float("inf"), float("-inf")) or not low <= value <= high:
        raise ForecastV2RequestError(f"{name} must be between {low} and {high}.")
    return float(value)


def _int(value: Any, name: str, *, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ForecastV2RequestError(f"{name} must be an integer between {low} and {high}.")
    return value


def _ids(raw: Any, name: str) -> Optional[list[str]]:
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ForecastV2RequestError(f"{name} must be a list.")
    return [str(item) for item in raw if str(item).strip()]


def _adjustments(raw: Any, name: str) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list) or len(raw) > MAX_ADJUSTMENTS:
        raise ForecastV2RequestError(f"{name} must be a list of at most {MAX_ADJUSTMENTS} items.")
    if not all(isinstance(item, dict) for item in raw):
        raise ForecastV2RequestError(f"{name} entries must be objects.")
    return [dict(item) for item in raw]


def _parse_request(payload: dict[str, Any], today: date) -> dict[str, Any]:
    user_id = str(payload.get("user_id") or "").strip()
    if not user_id:
        raise ForecastV2RequestError("user_id is required.")
    raw_start = payload.get("start_date")
    try:
        start = datetime.fromisoformat(raw_start).date() if raw_start else today
    except (TypeError, ValueError) as exc:
        raise ForecastV2RequestError("start_date must be ISO-8601 formatted (YYYY-MM-DD).") from exc
    if not today - timedelta(days=730) <= start <= today + timedelta(days=365):
        raise ForecastV2RequestError("start_date must be within two years back and one year ahead.")
    horizon = _int(payload.get("horizon_days", 30), "horizon_days", low=1, high=MAX_HORIZON_DAYS)

    simulation = payload.get("simulation") or {}
    if not isinstance(simulation, dict):
        raise ForecastV2RequestError("simulation must be an object.")
    sim = {
        "enabled": bool(simulation.get("enabled", False)),
        "count": _int(simulation.get("count", DEFAULT_SIMULATIONS), "simulation.count", low=1, high=MAX_SIMULATIONS),
        "seed": _int(simulation.get("seed", DEFAULT_SEED), "simulation.seed", low=-(2**31), high=2**31),
        "threshold": _number(simulation.get("cash_threshold", 0), "simulation.cash_threshold", low=0, high=1e9),
    }

    raw_scenarios = payload.get("scenarios") or []
    if not isinstance(raw_scenarios, list) or len(raw_scenarios) > MAX_SCENARIOS:
        raise ForecastV2RequestError(f"scenarios must be a list of at most {MAX_SCENARIOS} items.")
    scenarios, seen = [], {"baseline"}
    for item in raw_scenarios:
        if not isinstance(item, dict):
            raise ForecastV2RequestError("scenario entries must be objects.")
        scenario_id = str(item.get("id") or "").strip()
        if not scenario_id or len(scenario_id) > 40:
            raise ForecastV2RequestError("scenario id is required (max 40 characters).")
        changes = item.get("changes") or {}
        if not isinstance(changes, dict) or set(changes) - SCENARIO_KEYS:
            unknown = sorted(set(changes) - SCENARIO_KEYS) if isinstance(changes, dict) else ["changes"]
            raise ForecastV2RequestError(f"Unsupported scenario changes: {', '.join(unknown)}.")
        parsed = {}
        if "residual_spending_multiplier" in changes:
            parsed["residual_spending_multiplier"] = _number(
                changes["residual_spending_multiplier"], "residual_spending_multiplier", low=0, high=3
            )
        if "income_multiplier" in changes:
            parsed["income_multiplier"] = _number(changes["income_multiplier"], "income_multiplier", low=0, high=3)
        if "delay_income_days" in changes:
            parsed["delay_income_days"] = _int(changes["delay_income_days"], "delay_income_days", low=0, high=60)
        parsed["adjustments"] = _adjustments(changes.get("adjustments"), "scenario adjustments")
        if scenario_id == "baseline":
            if any(v for k, v in parsed.items()):
                raise ForecastV2RequestError("The baseline scenario cannot have changes.")
            continue
        if scenario_id in seen:
            raise ForecastV2RequestError(f"Duplicate scenario id: {scenario_id}.")
        seen.add(scenario_id)
        scenarios.append({"id": scenario_id, "label": str(item.get("label") or scenario_id)[:80], "changes": parsed})

    return {
        "user_id": user_id,
        "start": start,
        "horizon": horizon,
        "included": _ids(payload.get("included_account_ids"), "included_account_ids"),
        "excluded": _ids(payload.get("excluded_account_ids"), "excluded_account_ids") or [],
        "adjustments": _adjustments(payload.get("adjustments"), "adjustments"),
        "scenarios": scenarios,
        "requested_scenarios": bool(raw_scenarios),
        "simulation": sim,
    }


def _authorize(user_id: str, included: Optional[list[str]]) -> None:
    """Fail closed when any explicitly requested account is not owned by ``user_id``."""
    if not included:
        return
    owned = {
        row.account_id
        for row in Account.query.filter(Account.account_id.in_(included), Account.user_id == user_id).all()
    }
    if set(included) - owned:
        raise ForecastV2AccessError("One or more requested accounts are not available to this user.")


# --------------------------------------------------------------------------- scenarios


def _scaled(event: ForecastV2Event, factor: float, **changes: Any) -> ForecastV2Event:
    amount = (event.amount * Decimal(str(factor))).quantize(CENT, rounding=ROUND_HALF_EVEN)
    return dataclasses.replace(event, amount=amount, **changes)


def _apply_scenario(
    inputs: dict[str, Any], adjustments: list[dict[str, Any]], changes: dict[str, Any]
) -> tuple[list[ForecastV2Event], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(events, residual_history, adjustments)`` copies with the scenario applied."""
    spend_factor = changes.get("residual_spending_multiplier")
    income_factor = changes.get("income_multiplier")
    delay = int(changes.get("delay_income_days") or 0)
    events: list[ForecastV2Event] = []
    for event in inputs["scheduled_events"]:
        if event.kind == "scheduled_income":
            if income_factor is not None:
                event = _scaled(event, income_factor)
            if delay:
                event = dataclasses.replace(
                    event, date=event.date + timedelta(days=delay), event_id=f"{event.event_id}+delay{delay}"
                )
        events.append(event)
    for event in inputs["residual_events"]:
        component = event.metadata.get("component")
        if component == "spend" and spend_factor is not None:
            event = _scaled(event, spend_factor)
        elif component == "income" and income_factor is not None:
            event = _scaled(event, income_factor)
        events.append(event)
    history = []
    for row in inputs["residual_history"]:
        spend, income = Decimal(row["spend"]), Decimal(row["income"])
        if spend_factor is not None:
            spend = (spend * Decimal(str(spend_factor))).quantize(CENT, rounding=ROUND_HALF_EVEN)
        if income_factor is not None:
            income = (income * Decimal(str(income_factor))).quantize(CENT, rounding=ROUND_HALF_EVEN)
        history.append({**row, "spend": str(spend), "income": str(income)})
    return events, history, adjustments + list(changes.get("adjustments") or [])


# --------------------------------------------------------------------------- serialization


def _event_row(event: ForecastV2Event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "kind": event.kind,
        "source": event.source,
        "source_id": event.source_id,
        "amount": float(event.amount),
        "account_id": event.account_id,
    }


def _liquidity(ledger: Any) -> dict[str, Any]:
    summary = ledger.summary
    return {
        "starting_cash": summary["starting_cash"],
        "ending_cash": summary["ending_cash"],
        "min_cash": summary["min_cash"],
        "min_cash_date": summary["min_cash_date"],
        "first_shortfall_date": summary["first_negative_date"],
    }


def _scenario_row(
    scenario: dict[str, Any],
    ledger: Any,
    baseline: Any,
    risk: Optional[dict[str, Any]],
    base_risk: Optional[dict[str, Any]],
) -> dict[str, Any]:
    liquidity = _liquidity(ledger)
    row: dict[str, Any] = {
        "id": scenario["id"],
        "label": scenario["label"],
        "changes": scenario.get("changes", {}),
        **{k: liquidity[k] for k in ("ending_cash", "min_cash", "min_cash_date", "first_shortfall_date")},
        "delta_vs_baseline": {
            "ending_cash": round(liquidity["ending_cash"] - baseline.summary["ending_cash"], 2),
            "min_cash": round(liquidity["min_cash"] - baseline.summary["min_cash"], 2),
        },
        "timeline": [{"date": p.date.isoformat(), "liquid_cash": float(p.ending_cash)} for p in ledger.daily],
        "risk": None,
    }
    if risk is not None:
        row["risk"] = {
            **risk,
            "delta_vs_baseline": (
                {
                    key: round(risk[key] - base_risk[key], 4)
                    for key in ("probability_cash_below_zero_any_day", "probability_cash_below_threshold_any_day")
                }
                if base_risk
                else None
            ),
        }
    return row


def _series(ledger: Any) -> dict[str, Any]:
    def build(series_id: str, label: str, values: list[float]) -> dict[str, Any]:
        return {
            "id": series_id,
            "label": label,
            "points": [
                {"date": p.date.isoformat(), "label": p.date.isoformat(), "value": value, "metadata": {}}
                for p, value in zip(ledger.daily, values)
            ],
            "metadata": {"timeframe": "forecast", "source": "v2_ledger"},
        }

    return {
        "realized_income": build("realized_income", "Projected income", [float(p.inflows) for p in ledger.daily]),
        "manual_adjustments": build(
            "manual_adjustments", "Manual adjustments", [float(p.adjustments) for p in ledger.daily]
        ),
        "spending": build("spending", "Spending", [-float(p.outflows) for p in ledger.daily]),
        "debt_totals": build("debt_totals", "Debt totals", [float(p.liability_balance) for p in ledger.daily]),
    }


def _drivers(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    streams = {s["stream_id"]: s for s in inputs["streams"]}
    rows = []
    for event in inputs["scheduled_events"]:
        stream = streams.get(str(event.source_id), {})
        origin = stream.get("origin", "manual")
        level = (
            "high"
            if origin in {"manual", "recurring_rule", "inferred_confirmed"}
            else stream.get("confidence_level", "low")
        )
        rows.append(
            {
                "event_id": event.event_id,
                "source_id": event.source_id,
                "date": event.date.isoformat(),
                "amount": float(event.amount),
                "kind": event.kind,
                "origin": _ORIGIN_LABELS.get(origin, origin),
                "confidence_label": level,
                "label": event.metadata.get("label"),
                "account_id": event.account_id,
            }
        )
    return sorted(rows, key=lambda r: (r["date"], r["event_id"]))[:MAX_DRIVERS]


def _empty_response(
    parsed: dict[str, Any], as_of: date, warnings: list[dict[str, Any]], inputs: dict[str, Any]
) -> dict[str, Any]:
    """Transparent degradation when no liquid-cash anchor exists."""
    return {
        "model_version": MODEL_VERSION,
        "status": "insufficient_data",
        "timeline": [],
        "summary": None,
        "cashflows": [],
        "adjustments": [],
        "series": {},
        "metadata": {"model_version": MODEL_VERSION, "horizon_days": parsed["horizon"]},
        "liquidity": None,
        "net_worth": None,
        "uncertainty": {"available": False, "reason": "no_liquid_cash_accounts"},
        "drivers": [],
        "data_quality": {
            "as_of_date": as_of.isoformat(),
            "history_days": inputs["coverage"]["history_days"],
            "warnings": warnings,
        },
        "scenarios": [],
    }


# --------------------------------------------------------------------------- public API


def compute_v2_forecast(payload: dict[str, Any], *, today: Optional[date] = None) -> dict[str, Any]:
    """Compute the V2 forecast response for one user.

    Raises:
        ForecastV2RequestError: invalid parameters (400).
        ForecastV2AccessError: requested accounts not owned by the user (403).
    """
    parsed = _parse_request(payload, today or date.today())
    user_id, start, horizon = parsed["user_id"], parsed["start"], parsed["horizon"]
    _authorize(user_id, parsed["included"])
    as_of = start - timedelta(days=1)

    try:
        data = load_v2_source_data(
            user_id=user_id,
            as_of_date=as_of,
            included_account_ids=parsed["included"],
            excluded_account_ids=parsed["excluded"],
        )
        warnings: list[dict[str, Any]] = []
        accounts = []
        for account in data["accounts"]:
            account = dict(account)
            if (
                account["balance"] is None
                and start >= (today or date.today())
                and account.get("current_balance") is not None
            ):
                # Only for present/future starts: the live balance is the best available anchor.
                account["balance"], account["as_of"] = account["current_balance"], as_of
                warnings.append(
                    {
                        "code": "anchored_to_current_balance",
                        "message": "No snapshot on or before the as-of date; used the account's current balance.",
                        "account_id": account["account_id"],
                    }
                )
            accounts.append(account)
        inputs = build_v2_inputs(
            transactions=data["transactions"],
            recurring_rules=data["recurring_rules"],
            accounts=accounts,
            as_of_date=as_of,
            start_date=start,
            horizon_days=horizon,
        )

        def run_ledger(events: Iterable[ForecastV2Event], adjustments: list[dict[str, Any]]) -> Any:
            return simulate_cash_ledger(
                start_date=start,
                horizon_days=horizon,
                account_snapshots=accounts,
                events=list(events),
                cash_adjustments=adjustments,
                owner_id=user_id,
            )

        base_events = inputs["scheduled_events"] + inputs["residual_events"]
        baseline = run_ledger(base_events, parsed["adjustments"])
        if data["ignored_account_ids"]:
            warnings.append(
                {
                    "code": "accounts_ignored",
                    "message": "Some requested accounts were not found.",
                    "count": len(data["ignored_account_ids"]),
                }
            )
        if baseline.status != "ok":
            return _empty_response(parsed, as_of, warnings + baseline.warnings, inputs)

        sim = parsed["simulation"]

        def simulate(events: list[ForecastV2Event], history: list[dict[str, Any]], adjustments: list[dict[str, Any]]):
            scheduled = [e for e in events if e.source != "residual"]
            residual = [e for e in events if e.source == "residual"]
            return simulate_v2_paths(
                start_date=start,
                horizon_days=horizon,
                account_snapshots=accounts,
                scheduled_events=scheduled,
                residual_events=residual,
                residual_history=history,
                cash_adjustments=adjustments,
                simulation_count=sim["count"],
                seed=sim["seed"],
                threshold=sim["threshold"],
                owner_id=user_id,
            )

        uncertainty = {"available": False, "reason": "simulation_disabled"}
        bands: dict[str, dict[str, Any]] = {}
        base_risk: Optional[dict[str, Any]] = None
        if sim["enabled"]:
            result = simulate(base_events, inputs["residual_history"], parsed["adjustments"])
            if result.uncertainty_available:
                bands = {b["date"]: b for b in result.bands}
                base_risk = {
                    "probability_cash_below_zero_any_day": result.risk["probability_cash_below_zero_any_day"],
                    "probability_cash_below_threshold_any_day": result.risk["probability_cash_below_threshold_any_day"],
                }
                uncertainty = {
                    "available": True,
                    "risk_below_zero_any_day": base_risk["probability_cash_below_zero_any_day"],
                    "risk_below_threshold_any_day": base_risk["probability_cash_below_threshold_any_day"],
                    "threshold": result.risk["threshold"],
                    "sample_count": result.simulation_count,
                    "seed": result.seed,
                    "history_coverage_days": result.history_coverage_days,
                    "method": result.assumptions.get("method"),
                    "interval": "P10-P90 of simulated liquid cash; model output, not a guarantee",
                }
            else:
                uncertainty = {"available": False, "reason": result.reason}

        scenario_rows: list[dict[str, Any]] = []
        if parsed["requested_scenarios"]:
            scenario_rows.append(
                _scenario_row({"id": "baseline", "label": "Baseline"}, baseline, baseline, base_risk, None)
            )
            for scenario in parsed["scenarios"]:
                events, history, adjustments = _apply_scenario(inputs, parsed["adjustments"], scenario["changes"])
                ledger = run_ledger(events, adjustments)
                risk = None
                if base_risk is not None:
                    scenario_result = simulate(events, history, adjustments)
                    if scenario_result.uncertainty_available:
                        risk = {
                            "probability_cash_below_zero_any_day": scenario_result.risk[
                                "probability_cash_below_zero_any_day"
                            ],
                            "probability_cash_below_threshold_any_day": scenario_result.risk[
                                "probability_cash_below_threshold_any_day"
                            ],
                        }
                scenario_rows.append(_scenario_row(scenario, ledger, baseline, risk, base_risk))
    except ForecastV2InputError as exc:
        raise ForecastV2RequestError(str(exc)) from exc

    summary = baseline.summary
    first = baseline.daily[0]
    last = baseline.daily[-1]
    timeline = []
    for point in baseline.daily:
        row: dict[str, Any] = {
            "date": point.date.isoformat(),
            "label": point.date.isoformat(),
            "forecast_balance": float(point.ending_cash),  # liquid cash, not net worth
            "liquid_cash": float(point.ending_cash),
            "actual_balance": None,
            "delta": None,
            "metadata": {},
        }
        band = bands.get(row["date"])
        if band:
            row.update(p10=band["p10"], p50=band["p50"], p90=band["p90"])
        if point.event_ids:
            row["events"] = point.event_ids
        timeline.append(row)

    cashflows = [
        {
            "date": e.date.isoformat(),
            "amount": float(e.amount),
            "label": e.metadata.get("label") or e.kind.replace("_", " "),
            "category": e.kind,
            "source": e.source,
            "type": "income" if e.amount > 0 else "expense",
            "confidence": e.confidence,
            "account_id": None,
            "recurring_id": None,
            "direction": "inflow" if e.amount > 0 else "outflow",
            "sources": None,
            "metadata": {"event_id": e.event_id, "source_id": e.source_id},
        }
        for e in baseline.events
    ]
    quality_warnings = warnings + baseline.warnings
    return {
        "model_version": MODEL_VERSION,
        "status": "ok",
        "timeline": timeline,
        "summary": {
            "start_date": start.isoformat(),
            "end_date": baseline.end_date.isoformat(),
            "starting_balance": summary["starting_cash"],
            "ending_balance": summary["ending_cash"],
            "net_change": summary["net_change"],
            "total_inflows": summary["total_inflows"],
            "total_outflows": summary["total_outflows"],
            "average_daily_change": round(summary["net_change"] / horizon, 2),
            "min_balance": summary["min_cash"],
            "max_balance": summary["max_cash"],
            "depletion_date": summary["first_negative_date"],
            "currency": summary["currency"],
            "breakdowns": summary["by_kind"],
            "account_count": len(baseline.accounts["included"]["cash"]),
            "recurring_count": sum(1 for s in inputs["streams"] if s["status"] == "promoted"),
            "metadata": {"balance_basis": "liquid_cash"},
        },
        "cashflows": cashflows,
        "adjustments": [
            {
                "label": str(a.get("label") or "Adjustment"),
                "amount": float(a.get("amount") or 0),
                "date": a.get("date") or a.get("range_start"),
                "adjustment_type": "manual",
                "reason": a.get("reason"),
                "adjustment_id": a.get("adjustment_id") or a.get("id"),
                "metadata": {},
            }
            for a in parsed["adjustments"]
        ],
        "series": _series(baseline),
        "metadata": {
            "model_version": MODEL_VERSION,
            "balance_basis": "liquid_cash",
            "starting_balance": summary["starting_cash"],
            "included_account_ids": parsed["included"],
            "excluded_account_ids": parsed["excluded"],
            "account_buckets": baseline.accounts["included"],
            "horizon_days": horizon,
            "start_date": start.isoformat(),
        },
        "liquidity": _liquidity(baseline),
        "net_worth": {
            "starting": summary["starting_net_worth"],
            "ending": summary["ending_net_worth"],
            "liabilities": {"starting": float(first.liability_balance), "ending": float(last.liability_balance)},
            "investments": {"starting": float(first.investment_value), "ending": float(last.investment_value)},
        },
        "uncertainty": uncertainty,
        "drivers": _drivers(inputs),
        "data_quality": {
            "as_of_date": as_of.isoformat(),
            "history_days": inputs["coverage"]["history_days"],
            "confidence": inputs["coverage"]["confidence"],
            "residual_model": inputs["coverage"]["residual_model"],
            "proposed_streams": len(inputs["proposed_rules"]),
            "warnings": quality_warnings,
        },
        "scenarios": scenario_rows,
    }
