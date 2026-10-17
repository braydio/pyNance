"""Database adapter for Forecast V2 sources.

Reads one user's accounts, posted history, saved recurring rules and balance snapshots **as of a
date** (never later), then hands plain dicts to the pure ``forecast.v2_sources`` pipeline. It never
mutates transactions or recurring rules.

Ownership contract: every query is scoped to ``user_id``. ``included_account_ids`` can only narrow
the user's own accounts; ids that belong to someone else are ignored and reported in
``ignored_account_ids`` rather than read.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable, Optional

from forecast.v2_sources import DEFAULT_OPTIONS, build_v2_inputs, normalize_merchant_key

from app.models import Account, AccountHistory, RecurringStream, RecurringTransaction, Transaction
from app.services.transaction_semantics import account_bucket, normalize_amount


def _as_date(value: date | str) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def load_v2_source_data(
    *,
    user_id: str,
    as_of_date: date | str,
    included_account_ids: Optional[Iterable[str]] = None,
    excluded_account_ids: Optional[Iterable[str]] = None,
    lookback_days: int = DEFAULT_OPTIONS["stream_lookback_days"],
) -> dict[str, Any]:
    """Load accounts, transactions, saved rules and as-of balances for one user.

    Args:
        user_id: Owner. Required; an empty value raises ``ValueError`` instead of reading everything.
        as_of_date: Last allowed data date. Transactions and snapshots after it are not loaded.
        included_account_ids: Optional narrowing of the user's accounts.
        excluded_account_ids: Optional accounts to leave out.
        lookback_days: History window length ending at ``as_of_date``.

    Returns:
        ``{"accounts", "transactions", "recurring_rules", "ignored_account_ids", "as_of_date"}``.
        ``transactions`` carry the canonical ``amount`` (``+`` inflow / ``-`` outflow, see
        ``transaction_semantics``) plus ``raw_amount``, ``amount_semantics``, ``account_bucket`` and
        ``source_provider`` for audit; rows whose sign cannot be determined are left out and counted
        in ``sign_summary`` instead of being assumed to be expenses.
        Each account carries ``balance``/``as_of`` from ``AccountHistory`` on or before
        ``as_of_date``; ``balance`` is ``None`` when no snapshot exists (today's balance is
        deliberately not substituted).
    """
    if not user_id:
        raise ValueError("user_id is required for forecast source loading")
    as_of = _as_date(as_of_date)
    window_start = as_of - timedelta(days=int(lookback_days) - 1)
    wanted = {str(a) for a in included_account_ids} if included_account_ids else None
    skipped = {str(a) for a in excluded_account_ids or ()}

    owned = (
        Account.query.filter(Account.user_id == user_id)
        .filter((Account.is_hidden.is_(False)) | (Account.is_hidden.is_(None)))
        .order_by(Account.account_id)
        .all()
    )
    owned_ids = {a.account_id for a in owned}
    ignored = sorted((wanted or set()) - owned_ids)
    accounts_rows = [a for a in owned if (wanted is None or a.account_id in wanted) and a.account_id not in skipped]
    ids = [a.account_id for a in accounts_rows]
    if not ids:
        return {
            "accounts": [],
            "transactions": [],
            "recurring_rules": [],
            "ignored_account_ids": ignored,
            "as_of_date": as_of,
            "sign_summary": {"normalized": 0, "excluded": 0, "by_reason": {}},
        }

    snapshots: dict[str, AccountHistory] = {}
    history = (
        AccountHistory.query.filter(AccountHistory.account_id.in_(ids), AccountHistory.date <= as_of)
        .filter((AccountHistory.user_id == user_id) | (AccountHistory.user_id.is_(None)))
        .order_by(AccountHistory.account_id, AccountHistory.date)
        .all()
    )
    for row in history:  # ascending date, so the last row per account wins
        snapshots[row.account_id] = row

    accounts = [
        {
            "account_id": a.account_id,
            "name": a.name,
            "type": a.type,
            "subtype": a.subtype,
            "is_investment": bool(a.is_investment),
            "is_hidden": bool(a.is_hidden),
            "user_id": a.user_id,
            "balance": snapshots[a.account_id].balance if a.account_id in snapshots else None,
            "current_balance": a.balance,
            "as_of": snapshots[a.account_id].date if a.account_id in snapshots else None,
        }
        for a in accounts_rows
    ]

    transactions = (
        Transaction.query.filter(Transaction.account_id.in_(ids))
        .filter((Transaction.user_id == user_id) | (Transaction.user_id.is_(None)))
        .filter(Transaction.date >= window_start, Transaction.date <= as_of)
        .order_by(Transaction.date, Transaction.transaction_id)
        .all()
    )
    buckets = {a["account_id"]: account_bucket(a) for a in accounts}
    tx_dicts = []
    excluded_by_reason: dict[str, int] = {}
    for t in transactions:
        provider = getattr(t.provider, "value", t.provider)
        semantics = normalize_amount(provider=provider, raw_amount=t.amount)
        if semantics.delta is None:
            excluded_by_reason[semantics.warning] = excluded_by_reason.get(semantics.warning, 0) + 1
            continue
        tx_dicts.append(
            {
                "transaction_id": t.transaction_id,
                "account_id": t.account_id,
                "date": t.date,
                "amount": semantics.delta,
                "raw_amount": t.amount,
                "amount_semantics": semantics.semantics,
                "account_bucket": buckets.get(t.account_id),
                "source_provider": str(provider),
                "name": t.description,
                "merchant_name": t.merchant_name if t.merchant_name != "Unknown" else None,
                "merchant_slug": t.merchant_slug,
                "category_slug": t.category_slug,
                "pending": bool(t.pending),
                "is_internal": bool(t.is_internal),
                "internal_match_id": t.internal_match_id,
                "transfer_type": t.transfer_type,
            }
        )
    sign_summary = {
        "normalized": len(tx_dicts),
        "excluded": sum(excluded_by_reason.values()),
        "by_reason": excluded_by_reason,
    }

    rules = []
    saved = (
        RecurringTransaction.query.filter(RecurringTransaction.account_id.in_(ids))
        .order_by(RecurringTransaction.id)
        .all()
    )
    for rule in saved:
        source = rule.transaction
        if source is None:
            continue
        rule_sign = normalize_amount(
            provider=getattr(source.provider, "value", source.provider), raw_amount=source.amount
        )
        if rule_sign.delta is None:
            continue
        rules.append(
            {
                "rule_id": f"recurring:{rule.id}",
                "account_id": rule.account_id,
                "merchant_key": normalize_merchant_key(
                    {
                        "merchant_slug": source.merchant_slug,
                        "merchant_name": source.merchant_name if source.merchant_name != "Unknown" else None,
                        "description": source.description,
                    }
                ),
                "amount": rule_sign.delta,
                "cadence": rule.frequency,
                "anchor_date": rule.next_due_date,
                "source_transaction_ids": [source.transaction_id],
            }
        )
    # Confirmed payment plans (cash account -> card/loan) are the only streams that can settle debt.
    payments = (
        RecurringStream.query.filter_by(user_id=user_id, status="confirmed", event_role="liability_payment")
        .filter(RecurringStream.funding_account_id.in_(ids) | RecurringStream.destination_account_id.in_(ids))
        .order_by(RecurringStream.id)
        .all()
    )
    for plan in payments:
        rules.append(
            {
                "rule_id": f"stream:{plan.id}",
                "account_id": plan.funding_account_id,
                "amount": plan.amount_cash_delta,
                "cadence": plan.cadence,
                "anchor_date": plan.anchor_date,
                "label": plan.display_name,
                "event_role": "liability_payment",
                "funding_account_id": plan.funding_account_id,
                "destination_account_id": plan.destination_account_id,
                "source_transaction_ids": [],
            }
        )
    return {
        "accounts": accounts,
        "transactions": tx_dicts,
        "recurring_rules": rules,
        "ignored_account_ids": ignored,
        "as_of_date": as_of,
        "sign_summary": sign_summary,
    }


def build_user_v2_inputs(
    *,
    user_id: str,
    as_of_date: date | str,
    horizon_days: int,
    included_account_ids: Optional[Iterable[str]] = None,
    excluded_account_ids: Optional[Iterable[str]] = None,
    manual_rules: Iterable[Any] = (),
    disabled_source_ids: Iterable[str] = (),
    confirmed_source_ids: Iterable[str] = (),
    options: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Load one user's data as of ``as_of_date`` and run the pure V2 sources pipeline.

    Projection starts the day after ``as_of_date``. The result adds ``account_snapshots`` (feed to
    ``simulate_cash_ledger``) and ``ignored_account_ids`` to the pipeline output.
    """
    opts = {**DEFAULT_OPTIONS, **(options or {})}
    data = load_v2_source_data(
        user_id=user_id,
        as_of_date=as_of_date,
        included_account_ids=included_account_ids,
        excluded_account_ids=excluded_account_ids,
        lookback_days=max(int(opts["lookback_days"]), int(opts["stream_lookback_days"])),
    )
    as_of = data["as_of_date"]
    result = build_v2_inputs(
        transactions=data["transactions"],
        recurring_rules=data["recurring_rules"],
        manual_rules=manual_rules,
        accounts=data["accounts"],
        as_of_date=as_of,
        start_date=as_of + timedelta(days=1),
        horizon_days=horizon_days,
        disabled_source_ids=disabled_source_ids,
        confirmed_source_ids=confirmed_source_ids,
        options=opts,
    )
    result["account_snapshots"] = data["accounts"]
    result["ignored_account_ids"] = data["ignored_account_ids"]
    result["sign_summary"] = data["sign_summary"]
    return result


__all__ = ["build_user_v2_inputs", "load_v2_source_data"]
