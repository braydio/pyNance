"""CLI: Import Account rows from a CSV dump into the database.

Expected CSV columns (extra columns are ignored):
    account_id,user_id,name,type,subtype,institution_name,status,balance,link_type,is_hidden,institution_db_id

Usage (from `backend/` directory):
    flask import-accounts --csv-path app/data/Accounts.csv
"""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import click
from app.extensions import db
from app.models import Account
from app.sql.account_logic import normalize_account_status
from flask.cli import with_appcontext


@click.command("import-accounts")
@click.option(
    "--csv-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=Path("app/data/Accounts.csv"),
    show_default=True,
    help="Path to Accounts.csv export.",
)
@with_appcontext
def import_accounts(csv_path: Path) -> None:
    """Upsert Account rows from a CSV export."""
    if not csv_path.exists():
        click.echo(f"CSV file not found: {csv_path}")
        return

    created = 0
    updated = 0
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

            account = Account.query.filter_by(account_id=account_id).first()
            if account:
                updated += 1
            else:
                account = Account(account_id=account_id)
                db.session.add(account)
                created += 1

            account.user_id = (row.get("user_id") or "").strip() or None
            account.name = (row.get("name") or "").strip() or "Unnamed Account"
            account.type = (row.get("type") or "").strip() or None
            account.subtype = (row.get("subtype") or "").strip() or None
            account.institution_name = (
                (row.get("institution_name") or "").strip() or None
            )

            raw_status = (row.get("status") or "").strip()
            account.status = normalize_account_status(raw_status)

            raw_link_type = (row.get("link_type") or "").strip().lower() or "manual"
            if raw_link_type not in {"manual", "plaid"}:
                raw_link_type = "manual"
            account.link_type = raw_link_type

            raw_balance = (row.get("balance") or "").strip()
            if raw_balance:
                try:
                    account.balance = Decimal(raw_balance)
                except InvalidOperation:
                    # Leave existing balance unchanged if parsing fails
                    pass

            raw_hidden = str(row.get("is_hidden") or "").strip()
            account.is_hidden = raw_hidden in {"1", "true", "True", "yes", "YES"}

            raw_institution_db_id = (row.get("institution_db_id") or "").strip()
            if raw_institution_db_id:
                try:
                    account.institution_db_id = int(raw_institution_db_id)
                except ValueError:
                    account.institution_db_id = None

            # Preserve timestamps if present; otherwise let defaults apply
            raw_created = (row.get("created_at") or "").strip()
            raw_updated = (row.get("updated_at") or "").strip()
            for attr, raw_value in (
                ("created_at", raw_created),
                ("updated_at", raw_updated),
            ):
                if not raw_value:
                    continue
                try:
                    # CSV uses `YYYY-MM-DD HH:MM:SS.microseconds`
                    dt = datetime.fromisoformat(raw_value)
                    setattr(account, attr, dt)
                except ValueError:
                    # Ignore malformed timestamps
                    continue

    db.session.commit()

    click.echo("Accounts import complete.")
    click.echo(f"  Created: {created}")
    click.echo(f"  Updated: {updated}")
    click.echo(f"  Skipped (invalid/missing id): {skipped_invalid}")

