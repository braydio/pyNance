"""CLI: Import Plaid access tokens from a CSV dump.

Reads `account_id,access_token,item_id` rows and upserts:
- `PlaidItem` (secure token storage, keyed by `item_id`)
- `PlaidAccount` (linking Plaid items to local accounts)

Usage example (from `backend/` directory):

    flask --app backend.run import-plaid-tokens
    flask --app backend.run import-plaid-tokens --csv-path app/data/PlaidAccessTokens.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

import click
from app.extensions import db
from app.models import Account, PlaidAccount, PlaidItem
from flask.cli import with_appcontext


@click.command("import-plaid-tokens")
@click.option(
    "--csv-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path("app/data/PlaidAccessTokens.csv"),
    show_default=True,
    help="Path to CSV with account_id,access_token,item_id columns.",
)
@with_appcontext
def import_plaid_tokens(csv_path: Path) -> None:
    """Upsert Plaid tokens from a CSV export into the database."""
    if not csv_path.exists():
        click.echo(f"CSV file not found: {csv_path}")
        return

    created_items = 0
    updated_items = 0
    created_accounts = 0
    updated_accounts = 0
    skipped_missing_account = 0
    skipped_invalid_row = 0

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required_cols = {"account_id", "access_token", "item_id"}
        if not required_cols.issubset(set(reader.fieldnames or ())):
            click.echo(
                "CSV is missing required columns. "
                f"Expected {sorted(required_cols)}, got {reader.fieldnames}"
            )
            return

        for row in reader:
            account_id = (row.get("account_id") or "").strip()
            access_token = (row.get("access_token") or "").strip()
            item_id = (row.get("item_id") or "").strip()

            if not account_id or not access_token or not item_id:
                skipped_invalid_row += 1
                continue

            account = Account.query.filter_by(account_id=account_id).first()
            if not account:
                skipped_missing_account += 1
                continue

            # Upsert PlaidItem keyed by item_id
            plaid_item = PlaidItem.query.filter_by(item_id=item_id).first()
            if plaid_item:
                plaid_item.access_token = access_token
                if account.user_id:
                    plaid_item.user_id = str(account.user_id)
                plaid_item.is_active = True
                updated_items += 1
            else:
                plaid_item = PlaidItem(
                    user_id=str(account.user_id) if account.user_id else "import",
                    item_id=item_id,
                    access_token=access_token,
                    product="transactions",
                    is_active=True,
                )
                db.session.add(plaid_item)
                created_items += 1

            # Upsert PlaidAccount keyed by account_id
            plaid_account = PlaidAccount.query.filter_by(
                account_id=account_id
            ).first()
            if plaid_account:
                plaid_account.access_token = access_token
                plaid_account.item_id = item_id
                plaid_account.is_active = True
                updated_accounts += 1
            else:
                plaid_account = PlaidAccount(
                    account_id=account_id,
                    access_token=access_token,
                    item_id=item_id,
                    is_active=True,
                )
                db.session.add(plaid_account)
                created_accounts += 1

    db.session.commit()

    click.echo("Import complete.")
    click.echo(f"  PlaidItem created:   {created_items}")
    click.echo(f"  PlaidItem updated:   {updated_items}")
    click.echo(f"  PlaidAccount created:{created_accounts}")
    click.echo(f"  PlaidAccount updated:{updated_accounts}")
    click.echo(f"  Rows without account:{skipped_missing_account}")
    click.echo(f"  Rows invalid/missing:{skipped_invalid_row}")

