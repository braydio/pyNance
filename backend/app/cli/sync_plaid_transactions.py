"""CLI: Trigger Plaid transactions refreshes.

Usage:
- flask --app backend.run sync-plaid-tx              # sync all items
- flask --app backend.run sync-plaid-tx --item ITEM  # sync a specific item
- flask --app backend.run sync-plaid-tx --account ACC# sync a specific account
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

import click
from sqlalchemy.orm import joinedload

from app.config import logger
from app.extensions import db
from app.models import PlaidAccount
from app.sql import account_logic
from flask.cli import with_appcontext


def _refresh_plaid_account(pa: PlaidAccount) -> Tuple[bool, Optional[dict]]:
    """Run a Plaid refresh for a single account and update metadata."""

    result = account_logic.refresh_data_for_plaid_account(
        pa.access_token, pa.account_id
    )
    if isinstance(result, tuple) and len(result) == 2:
        updated, error = result
    else:
        updated, error = bool(result), None

    if error:
        db.session.rollback()
        return updated, error

    timestamp = datetime.now(timezone.utc)
    pa.last_refreshed = timestamp
    if pa.account:
        pa.account.updated_at = timestamp

    try:
        db.session.commit()
    except Exception as commit_err:  # pragma: no cover - defensive
        db.session.rollback()
        logger.error(
            "Failed to persist Plaid metadata for account %s: %s",
            pa.account_id,
            commit_err,
        )
        return updated, {
            "plaid_error_code": "metadata_commit_failed",
            "plaid_error_message": str(commit_err),
        }

    return updated, None


@click.command("sync-plaid-tx")
@click.option("--item", "item_id", help="Plaid item_id to sync")
@click.option("--account", "account_id", help="Account ID to sync")
@with_appcontext
def sync_plaid_tx(item_id: str | None, account_id: str | None) -> None:
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
            updated, error = _refresh_plaid_account(pa)
            if error:
                logger.error(
                    "Refresh failed for account %s: %s", pa.account_id, error
                )
                message = error.get("plaid_error_message") if isinstance(error, dict) else str(error)
                click.echo(f"ERR {pa.account_id}: {message}")
            else:
                click.echo(f"OK {pa.account_id}: updated={bool(updated)}")
            return

        if item_id:
            pa = (
                PlaidAccount.query.options(joinedload(PlaidAccount.account))
                .filter_by(item_id=item_id)
                .first()
            )
            if not pa:
                click.echo(f"No PlaidAccount for item {item_id}")
                return
            if not pa.access_token:
                click.echo(f"Plaid item {item_id} is missing an access token")
                return
            updated, error = _refresh_plaid_account(pa)
            if error:
                logger.error("Refresh failed for item %s: %s", item_id, error)
                message = error.get("plaid_error_message") if isinstance(error, dict) else str(error)
                click.echo(f"ERR {item_id}: {message}")
            else:
                click.echo(f"OK {item_id}: account={pa.account_id} updated={bool(updated)}")
            return

        # Default: sync one account per distinct item
        seen = set()
        updates = 0
        query = PlaidAccount.query.options(joinedload(PlaidAccount.account)).order_by(
            PlaidAccount.item_id
        )
        for pa in query.all():
            if not pa.item_id or pa.item_id in seen:
                continue
            seen.add(pa.item_id)
            try:
                if not pa.access_token:
                    click.echo(
                        f"ERR {pa.item_id}: missing access token for account {pa.account_id}"
                    )
                    logger.error(
                        "Skipping Plaid item %s due to missing access token", pa.item_id
                    )
                    continue

                updated, error = _refresh_plaid_account(pa)
                if error:
                    logger.error(
                        "Refresh failed for item %s account %s: %s",
                        pa.item_id,
                        pa.account_id,
                        error,
                    )
                    message = error.get("plaid_error_message") if isinstance(error, dict) else str(error)
                    click.echo(f"ERR {pa.item_id}: {message}")
                    continue

                updates += int(bool(updated))
                click.echo(
                    f"OK {pa.item_id}: account={pa.account_id} updated={bool(updated)}"
                )
            except Exception as e:
                logger.error(f"Sync failed for item {pa.item_id}: {e}")
                click.echo(f"ERR {pa.item_id}: {e}")
        click.echo(f"Completed. Items={len(seen)} updated_accounts={updates}")
    except Exception as e:
        logger.error(f"sync-plaid-tx error: {e}")
        click.echo(str(e))
