"""CLI: Trigger Plaid transactions/sync.

Usage:
- flask --app backend.run sync-plaid-tx              # sync all items
- flask --app backend.run sync-plaid-tx --item ITEM  # sync a specific item
- flask --app backend.run sync-plaid-tx --account ACC# sync a specific account
"""

import click
from app.config import logger
from app.models import PlaidAccount
from app.services.plaid_sync import sync_account_transactions
from flask.cli import with_appcontext


@click.command("sync-plaid-tx")
@click.option("--item", "item_id", help="Plaid item_id to sync")
@click.option("--account", "account_id", help="Account ID to sync")
@with_appcontext
def sync_plaid_tx(item_id: str | None, account_id: str | None) -> None:
    try:
        if account_id:
            res = sync_account_transactions(account_id)
            click.echo(res)
            return

        if item_id:
            pa = PlaidAccount.query.filter_by(item_id=item_id).first()
            if not pa:
                click.echo(f"No PlaidAccount for item {item_id}")
                return
            res = sync_account_transactions(pa.account_id)
            click.echo(res)
            return

        # Default: sync one account per distinct item
        seen = set()
        total = 0
        for pa in PlaidAccount.query.order_by(PlaidAccount.item_id).all():
            if not pa.item_id or pa.item_id in seen:
                continue
            seen.add(pa.item_id)
            try:
                res = sync_account_transactions(pa.account_id)
                total += res.get("added", 0) or 0
                click.echo(
                    f"OK {pa.item_id}: +{res.get('added', 0)}/~{res.get('modified', 0)} -{res.get('removed', 0)}"
                )
            except Exception as e:
                logger.error(f"Sync failed for item {pa.item_id}: {e}")
                click.echo(f"ERR {pa.item_id}: {e}")
        click.echo(f"Completed. Items={len(seen)} new_tx={total}")
    except Exception as e:
        logger.error(f"sync-plaid-tx error: {e}")
        click.echo(str(e))
