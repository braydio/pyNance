"""CLI: Backfill Plaid transaction history over a custom date range.

This reuses the existing :func:`refresh_data_for_plaid_account` helper, but lets you
specify an explicit start/end date so you can pull as much history as Plaid allows.

Usage examples (from `backend/` directory, with FLASK_APP=run.py):

    # Backfill a single account for the last 2 years
    flask backfill-plaid-history --account <ACCOUNT_ID> --start 2023-01-01

    # Backfill all accounts under a specific Item
    flask backfill-plaid-history --item <ITEM_ID> --start 2023-01-01

    # Backfill all Plaid accounts in the DB
    flask backfill-plaid-history --start 2023-01-01
"""

from __future__ import annotations

from datetime import date, datetime

import click
from app.config import logger
from app.models import PlaidAccount
from app.sql import account_logic
from flask.cli import with_appcontext
from sqlalchemy.orm import joinedload


def _parse_date(label: str, value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise click.BadParameter(
            f"{label} must be in YYYY-MM-DD format (got {value!r})"
        ) from exc


@click.command("backfill-plaid-history")
@click.option("--item", "item_id", help="Plaid item_id to backfill")
@click.option("--account", "account_id", help="Plaid account_id to backfill")
@click.option(
    "--start",
    "start_date",
    help="Start date (YYYY-MM-DD). If omitted, uses the internal default window.",
)
@click.option(
    "--end",
    "end_date",
    help="End date (YYYY-MM-DD). If omitted, uses today.",
)
@with_appcontext
def backfill_plaid_history(
    item_id: str | None, account_id: str | None, start_date: str | None, end_date: str | None
) -> None:
    """Backfill Plaid transactions over a custom date range."""
    start = _parse_date("start", start_date)
    end = _parse_date("end", end_date)

    if account_id and item_id:
        raise click.BadParameter("Provide either --account or --item, not both.")

    try:
        if account_id:
            pa = (
                PlaidAccount.query.options(joinedload(PlaidAccount.account))
                .filter_by(account_id=account_id)
                .first()
            )
            if not pa:
                click.echo(f"No PlaidAccount for account {account_id}")
                return
            if not pa.access_token:
                click.echo(f"Plaid account {account_id} is missing an access token")
                return

            click.echo(
                f"Backfilling account {pa.account_id} from "
                f"{start.isoformat() if start else '[default]'} "
                f"to {end.isoformat() if end else '[today]'}"
            )
            updated, error = account_logic.refresh_data_for_plaid_account(
                pa.access_token, pa.account_id, start_date=start, end_date=end
            )
            if error:
                logger.error(
                    "Backfill failed for account %s: %s", pa.account_id, error
                )
                message = (
                    error.get("plaid_error_message")
                    if isinstance(error, dict)
                    else str(error)
                )
                click.echo(f"ERR {pa.account_id}: {message}")
            else:
                click.echo(f"OK {pa.account_id}: updated={bool(updated)}")
            return

        if item_id:
            rows = (
                PlaidAccount.query.options(joinedload(PlaidAccount.account))
                .filter_by(item_id=item_id)
                .all()
            )
            if not rows:
                click.echo(f"No PlaidAccounts found for item {item_id}")
                return

            for pa in rows:
                if not pa.access_token:
                    click.echo(
                        f"ERR {pa.account_id}: missing access token for item {item_id}"
                    )
                    continue
                click.echo(
                    f"Backfilling account {pa.account_id} (item {item_id}) "
                    f"from {start.isoformat() if start else '[default]'} "
                    f"to {end.isoformat() if end else '[today]'}"
                )
                updated, error = account_logic.refresh_data_for_plaid_account(
                    pa.access_token, pa.account_id, start_date=start, end_date=end
                )
                if error:
                    logger.error(
                        "Backfill failed for item %s account %s: %s",
                        item_id,
                        pa.account_id,
                        error,
                    )
                    message = (
                        error.get("plaid_error_message")
                        if isinstance(error, dict)
                        else str(error)
                    )
                    click.echo(f"ERR {item_id}/{pa.account_id}: {message}")
                else:
                    click.echo(
                        f"OK {item_id}/{pa.account_id}: updated={bool(updated)}"
                    )
            return

        # Default: backfill all distinct Plaid items
        seen_items: set[str] = set()
        updates = 0
        query = PlaidAccount.query.options(joinedload(PlaidAccount.account)).order_by(
            PlaidAccount.item_id
        )
        for pa in query.all():
            if not pa.item_id or pa.item_id in seen_items:
                continue
            seen_items.add(pa.item_id)

            if not pa.access_token:
                click.echo(
                    f"ERR {pa.item_id}: missing access token for account {pa.account_id}"
                )
                logger.error(
                    "Skipping Plaid item %s due to missing access token", pa.item_id
                )
                continue

            click.echo(
                f"Backfilling item {pa.item_id} (account {pa.account_id}) "
                f"from {start.isoformat() if start else '[default]'} "
                f"to {end.isoformat() if end else '[today]'}"
            )
            updated, error = account_logic.refresh_data_for_plaid_account(
                pa.access_token, pa.account_id, start_date=start, end_date=end
            )
            if error:
                logger.error(
                    "Backfill failed for item %s account %s: %s",
                    pa.item_id,
                    pa.account_id,
                    error,
                )
                message = (
                    error.get("plaid_error_message")
                    if isinstance(error, dict)
                    else str(error)
                )
                click.echo(f"ERR {pa.item_id}: {message}")
                continue

            updates += int(bool(updated))
            click.echo(
                f"OK {pa.item_id}: account={pa.account_id} updated={bool(updated)}"
            )

        click.echo(f"Completed backfill. Items={len(seen_items)} updated_accounts={updates}")

    except Exception as e:  # pragma: no cover - defensive
        logger.error("backfill-plaid-history error: %s", e, exc_info=True)
        click.echo(str(e))

