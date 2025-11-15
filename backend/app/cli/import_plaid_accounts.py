"""CLI: Import PlaidAccount rows from a CSV dump into the database.

Expected CSV columns (extra columns are ignored):
    account_id,access_token,item_id,institution_id,webhook,last_refreshed,sync_cursor,is_active,last_error,plaid_institution_id,institution_db_id,product

Usage (from `backend/` directory):
    flask import-plaid-accounts --csv-path app/data/PlaidAccounts.csv
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import click
from app.extensions import db
from app.models import Account, PlaidAccount
from flask.cli import with_appcontext


@click.command("import-plaid-accounts")
@click.option(
    "--csv-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path("app/data/PlaidAccounts.csv"),
    show_default=True,
    help="Path to PlaidAccounts.csv export.",
)
@with_appcontext
def import_plaid_accounts(csv_path: Path) -> None:
    """Upsert PlaidAccount rows from a CSV export."""
    if not csv_path.exists():
        click.echo(f"CSV file not found: {csv_path}")
        return

    created = 0
    updated = 0
    skipped_missing_account = 0
    skipped_invalid = 0

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "account_id" not in reader.fieldnames:
            click.echo("CSV must include an 'account_id' column.")
            return

        for row in reader:
            account_id = (row.get("account_id") or "").strip()
            if not account_id:
                skipped_invalid += 1
                continue

            # Ensure the linked Account exists to maintain referential integrity
            if not Account.query.filter_by(account_id=account_id).first():
                skipped_missing_account += 1
                continue

            plaid_account = PlaidAccount.query.filter_by(
                account_id=account_id
            ).first()
            if plaid_account:
                updated += 1
            else:
                plaid_account = PlaidAccount(account_id=account_id)
                db.session.add(plaid_account)
                created += 1

            plaid_account.access_token = (
                (row.get("access_token") or "").strip() or None
            )
            plaid_account.item_id = (row.get("item_id") or "").strip() or None
            plaid_account.product = (row.get("product") or "").strip() or None
            plaid_account.institution_id = (
                (row.get("institution_id") or "").strip() or None
            )
            plaid_account.webhook = (row.get("webhook") or "").strip() or None
            plaid_account.sync_cursor = (
                (row.get("sync_cursor") or "").strip() or None
            )
            plaid_account.last_error = (row.get("last_error") or "").strip() or None

            raw_plaid_inst = (row.get("plaid_institution_id") or "").strip()
            plaid_account.plaid_institution_id = raw_plaid_inst or None

            raw_inst_db_id = (row.get("institution_db_id") or "").strip()
            if raw_inst_db_id:
                try:
                    plaid_account.institution_db_id = int(raw_inst_db_id)
                except ValueError:
                    plaid_account.institution_db_id = None

            raw_last_refreshed = (row.get("last_refreshed") or "").strip()
            if raw_last_refreshed:
                try:
                    plaid_account.last_refreshed = datetime.fromisoformat(
                        raw_last_refreshed
                    )
                except ValueError:
                    plaid_account.last_refreshed = None

            raw_active = str(row.get("is_active") or "").strip()
            plaid_account.is_active = raw_active not in {
                "0",
                "false",
                "False",
                "",
            }

            # Preserve created_at/updated_at when present
            raw_created = (row.get("created_at") or "").strip()
            raw_updated = (row.get("updated_at") or "").strip()
            for attr, raw_value in (
                ("created_at", raw_created),
                ("updated_at", raw_updated),
            ):
                if not raw_value:
                    continue
                try:
                    dt = datetime.fromisoformat(raw_value)
                    setattr(plaid_account, attr, dt)
                except ValueError:
                    continue

    db.session.commit()

    click.echo("PlaidAccounts import complete.")
    click.echo(f"  Created: {created}")
    click.echo(f"  Updated: {updated}")
    click.echo(f"  Skipped (missing Account): {skipped_missing_account}")
    click.echo(f"  Skipped (invalid/missing id): {skipped_invalid}")

