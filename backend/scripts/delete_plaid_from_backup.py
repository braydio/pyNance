#!/usr/bin/env python3
"""Delete Plaid-linked accounts based on a legacy SQLite backup.

This script reads the legacy dashboard SQLite database located under
``backend/app/data/`` and, for each account whose ``link_type`` is ``plaid``,
calls the backend's Plaid delete endpoint:

    DELETE /api/plaid/transactions/delete_account

The endpoint in turn revokes the Plaid item (via ``remove_item``) and deletes
the corresponding account and related records from the current PostgreSQL
database.

By default this runs in dry-run mode and only prints which accounts *would* be
deleted. Pass ``--execute`` to actually issue DELETE requests.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import requests


DEFAULT_SQLITE = Path("app/data/backup_dashboard_database.db")
DEFAULT_BASE_URL = "http://localhost:5000"


@dataclass
class BackupAccount:
    account_id: str
    name: str
    institution_name: str | None
    link_type: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=DEFAULT_SQLITE,
        help=(
            "Path to the legacy SQLite backup database "
            "(default: app/data/backup_dashboard_database.db)."
        ),
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL of the running backend (default: http://localhost:5000).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually call the delete endpoint. Without this, runs in dry-run mode.",
    )
    return parser.parse_args()


def load_plaid_accounts(sqlite_path: Path) -> List[BackupAccount]:
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite database not found: {sqlite_path}")

    conn = sqlite3.connect(sqlite_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT account_id, name, institution_name, link_type
            FROM accounts
            WHERE link_type = 'plaid'
            ORDER BY institution_name, name
            """
        )
        rows: Iterable[tuple] = cur.fetchall()
    finally:
        conn.close()

    accounts: List[BackupAccount] = []
    for account_id, name, institution_name, link_type in rows:
        if not account_id:
            continue
        accounts.append(
            BackupAccount(
                account_id=str(account_id),
                name=str(name),
                institution_name=str(institution_name) if institution_name else None,
                link_type=str(link_type) if link_type else None,
            )
        )
    return accounts


def delete_account(base_url: str, account_id: str) -> bool:
    url = base_url.rstrip("/") + "/api/plaid/transactions/delete_account"
    try:
        resp = requests.delete(url, json={"account_id": account_id}, timeout=10)
    except Exception as exc:  # pragma: no cover - operational guard
        print(f"[ERROR] Request failed for account_id={account_id}: {exc}")
        return False

    if resp.status_code != 200:
        print(
            f"[ERROR] Non-200 response for account_id={account_id}: "
            f"{resp.status_code} {resp.text}"
        )
        return False

    try:
        payload = resp.json()
    except ValueError:
        print(f"[WARN] Non-JSON response for account_id={account_id}: {resp.text}")
        return True

    status = payload.get("status")
    if status != "success":
        print(f"[WARN] Delete reported non-success for {account_id}: {payload}")
        return False

    print(f"[OK] Deleted account_id={account_id}")
    return True


def main() -> None:
    args = parse_args()
    accounts = load_plaid_accounts(args.sqlite_path)

    if not accounts:
        print(f"No plaid-linked accounts found in {args.sqlite_path}")
        return

    mode = "DRY RUN" if not args.execute else "EXECUTE"
    print(
        f"Found {len(accounts)} plaid-linked accounts in {args.sqlite_path} "
        f"({mode} mode)."
    )

    for acct in accounts:
        label = f"{acct.account_id} | {acct.name}"
        if acct.institution_name:
            label += f" @ {acct.institution_name}"

        if not args.execute:
            print(f"[DRY RUN] Would delete: {label}")
            continue

        print(f"Deleting: {label}")
        delete_account(args.base_url, acct.account_id)


if __name__ == "__main__":
    main()

