"""Developer CLI to prove Plaid transaction history coverage.

This module exposes a Flask CLI command that repeatedly calls Plaid's
``/transactions/get`` endpoint in rolling windows, deduplicates any overlapping
results, and prints a concise coverage report. It is intended for debugging and
verifying that we have downloaded the full transaction history Plaid makes
available for a specific account.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import click
from flask.cli import with_appcontext

FetchTransactions = Callable[[str, str, str], List[Dict[str, Any]]]
logger = logging.getLogger(__name__)


def _parse_date(label: str, value: str | None, default: date | None = None) -> date:
    """Parse ``value`` as a ``date`` in ``YYYY-MM-DD`` format.

    Args:
        label: User-facing label for error reporting.
        value: ISO date string or ``None``.
        default: Fallback date to return when ``value`` is empty.

    Raises:
        click.BadParameter: If the date cannot be parsed.

    Returns:
        Parsed ``date`` value.
    """

    if not value:
        if default:
            return default
        raise click.BadParameter(f"Missing required {label} date")

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:  # pragma: no cover - defensive guardrail
        raise click.BadParameter(
            f"{label} must be in YYYY-MM-DD format (got {value!r})"
        ) from exc


def collect_full_history(
    access_token: str,
    start_date: date,
    end_date: date,
    window_days: int = 180,
    fetcher: FetchTransactions | None = None,
) -> Dict[str, Any]:
    """Fetch and deduplicate Plaid transactions over a date range.

    The function iterates backwards from ``end_date`` in ``window_days`` chunks to
    avoid provider-level response limits. Each window is fetched independently and
    merged into a unique transaction set keyed by Plaid's ``transaction_id``.

    Args:
        access_token: Plaid access token for the account's item.
        start_date: Oldest date to request (inclusive).
        end_date: Latest date to request (inclusive).
        window_days: Size of each rolling window in days.
        fetcher: Optional override for fetching transactions. Defaults to
            :func:`app.helpers.plaid_helpers.get_transactions`.

    Returns:
        Dict summarizing the fetch, including window metadata, counts, and
        deduplicated transactions.
    """

    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")
    if window_days < 1:
        raise ValueError("window_days must be at least 1")

    fetch_transactions = fetcher
    if fetch_transactions is None:
        from app.helpers.plaid_helpers import get_transactions

        fetch_transactions = get_transactions

    all_transactions: Dict[str, Dict[str, Any]] = {}
    missing_ids: List[Dict[str, Any]] = []
    duplicate_ids = 0
    windows: List[Dict[str, Any]] = []
    total_seen = 0

    window_end = end_date
    while window_end >= start_date:
        window_start = max(start_date, window_end - timedelta(days=window_days - 1))
        window_label = f"{window_start.isoformat()} -> {window_end.isoformat()}"

        logger.info("[PLAID HISTORY] Fetching window %s", window_label)
        batch = fetch_transactions(
            access_token, window_start.isoformat(), window_end.isoformat()
        )
        total_seen += len(batch)

        for tx in batch:
            txn_id = tx.get("transaction_id")
            if txn_id:
                if txn_id in all_transactions:
                    duplicate_ids += 1
                    continue
                all_transactions[txn_id] = tx
            else:
                missing_ids.append(tx)

        windows.append({"start": window_start, "end": window_end, "count": len(batch)})

        if window_start == start_date:
            break

        window_end = window_start - timedelta(days=1)

    unique_transactions = sorted(
        all_transactions.values(), key=lambda tx: tx.get("date") or ""
    )
    combined_for_dates = sorted(
        unique_transactions + missing_ids, key=lambda tx: tx.get("date") or ""
    )
    earliest = combined_for_dates[0].get("date") if combined_for_dates else None
    latest = combined_for_dates[-1].get("date") if combined_for_dates else None

    return {
        "windows": windows,
        "total_seen": total_seen,
        "total_unique": len(unique_transactions) + len(missing_ids),
        "duplicate_transaction_ids": duplicate_ids,
        "missing_transaction_ids": len(missing_ids),
        "earliest_date": earliest,
        "latest_date": latest,
        "transactions": unique_transactions + missing_ids,
    }


@click.command("debug-plaid-history")
@click.option(
    "--account", "account_id", required=True, help="Plaid account_id to inspect"
)
@click.option(
    "--start",
    "start_date",
    default="2015-01-01",
    show_default=True,
    help="Earliest date to request (YYYY-MM-DD)",
)
@click.option(
    "--end",
    "end_date",
    default=None,
    help="Latest date to request (YYYY-MM-DD). Defaults to today when omitted.",
)
@click.option(
    "--window-days",
    default=180,
    show_default=True,
    help="Days per request window (helps avoid vendor response caps).",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    help="Optional path to dump unique transactions as JSON for inspection.",
)
@with_appcontext
def debug_plaid_history(
    account_id: str,
    start_date: str | None,
    end_date: str | None,
    window_days: int,
    output_path: str | None,
) -> None:
    """Dump the fullest Plaid transaction history available for an account."""

    today = datetime.utcnow().date()
    start = _parse_date("start", start_date)
    end = _parse_date("end", end_date, default=today)

    from app.models import PlaidAccount
    from sqlalchemy.orm import joinedload

    plaid_account = (
        PlaidAccount.query.options(joinedload(PlaidAccount.account))
        .filter_by(account_id=account_id)
        .first()
    )
    if not plaid_account:
        click.echo(f"No PlaidAccount found for account_id={account_id}")
        return
    if not plaid_account.access_token:
        click.echo(f"PlaidAccount {account_id} is missing an access token")
        return

    click.echo(
        f"Requesting Plaid history for account {account_id} from {start.isoformat()} "
        f"to {end.isoformat()} in {window_days}-day windows"
    )
    report = collect_full_history(
        access_token=plaid_account.access_token,
        start_date=start,
        end_date=end,
        window_days=window_days,
    )

    earliest = report.get("earliest_date") or "n/a"
    latest = report.get("latest_date") or "n/a"
    click.echo(
        f"Fetched {report['total_seen']} raw txns, {report['total_unique']} unique; "
        f"earliest={earliest}, latest={latest}, windows={len(report['windows'])}"
    )
    click.echo(
        f"Deduped {report['duplicate_transaction_ids']} duplicate transaction_ids; "
        f"{report['missing_transaction_ids']} rows lacked transaction_id"
    )

    click.echo("Suggested dedup guardrails:")
    click.echo(
        "- Use Plaid's transaction_id as the canonical key and update rows "
        "when amounts or status change."
    )
    click.echo(
        "- When transaction_id is missing, fall back to "
        "pending_transaction_id + date + amount + merchant_name."
    )
    click.echo(
        "- Keep the sync cursor current to reduce overlap and lower dedupe pressure."
    )

    if output_path:
        payload = {
            "account_id": account_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "window_days": window_days,
            "earliest_date": earliest,
            "latest_date": latest,
            "transactions": report["transactions"],
            "windows": [
                {
                    "start": w["start"].isoformat(),
                    "end": w["end"].isoformat(),
                    "count": w["count"],
                }
                for w in report["windows"]
            ],
        }
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
        click.echo(f"Wrote {len(report['transactions'])} transactions to {output_path}")
