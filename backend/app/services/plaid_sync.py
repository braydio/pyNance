"""Plaid Transactions Sync service.

Implements Plaid's delta-based transactions/sync flow. Applies added/modified/
removed transactions inside a single DB transaction and persists the cursor.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Tuple

from app.config import logger, plaid_client
from app.extensions import db
from app.models import Account, Category, PlaidAccount, Transaction
from app.sql import transaction_rules_logic
from app.sql.account_logic import (
    detect_internal_transfer,
    get_or_create_category,
    normalize_balance,
)
from app.sql.refresh_metadata import refresh_or_insert_plaid_metadata

try:
    # Plaid SDK v13+ style imports
    from plaid.model.transactions_sync_request import TransactionsSyncRequest
except Exception:  # pragma: no cover - allow older SDKs
    TransactionsSyncRequest = None  # type: ignore


def _parse_txn_date(val) -> datetime:
    if isinstance(val, datetime):
        # Ensure tz-aware in UTC
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    # Expect YYYY-MM-DD
    try:
        d = datetime.strptime(val, "%Y-%m-%d").date()
        return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
    except Exception:
        # Fallback to now to avoid crashing sync; log upstream parse issues
        logger.warning(f"[SYNC] Unexpected date format: {val!r}; defaulting to now()")
        return datetime.now(timezone.utc)


def _upsert_transaction(tx: dict, account: Account, plaid_acct: PlaidAccount) -> None:
    txn_id = tx.get("transaction_id")
    if not txn_id:
        return

    # Apply rules prior to persistence
    tx = transaction_rules_logic.apply_rules(account.user_id, dict(tx))

    # Map Plaid categories to local Category
    pfc = tx.get("personal_finance_category") or {}
    pfc_primary = pfc.get("primary") or "Unknown"
    pfc_detailed = pfc.get("detailed") or "Unknown"
    pfc_icon = tx.get("personal_finance_category_icon_url")

    legacy_path = tx.get("category") or []
    primary = legacy_path[0] if len(legacy_path) > 0 else "Unknown"
    detailed = legacy_path[1] if len(legacy_path) > 1 else "Unknown"

    category: Category = get_or_create_category(
        primary, detailed, pfc_primary, pfc_detailed, pfc_icon
    )

    # Normalize core fields
    txn_date = _parse_txn_date(tx.get("date"))
    description = tx.get("name") or tx.get("description") or "[no description]"
    merchant_name = tx.get("merchant_name") or "Unknown"
    merchant_type = (tx.get("payment_meta", {}) or {}).get(
        "payment_method"
    ) or "Unknown"
    pending = bool(tx.get("pending", False))

    existing = Transaction.query.filter_by(transaction_id=txn_id).first()
    if existing:
        changed = (
            existing.amount != tx.get("amount")
            or existing.date != txn_date
            or existing.description != description
            or existing.pending != pending
            or existing.category_id != category.id
            or existing.merchant_name != merchant_name
            or existing.merchant_type != merchant_type
        )
        if changed:
            existing.amount = tx.get("amount")
            existing.date = txn_date
            existing.description = description
            existing.pending = pending
            existing.category_id = category.id
            existing.category = category.display_name
            existing.merchant_name = merchant_name
            existing.merchant_type = merchant_type
            existing.provider = "Plaid"
            existing.personal_finance_category = pfc or None
            existing.personal_finance_category_icon_url = pfc_icon
        # Always refresh Plaid metadata (keeps aux fields current)
        refresh_or_insert_plaid_metadata(tx, existing, plaid_acct.account_id)
        detect_internal_transfer(existing)
    else:
        new_txn = Transaction(
            transaction_id=txn_id,
            amount=tx.get("amount"),
            date=txn_date,
            description=description,
            pending=pending,
            account_id=account.account_id,
            category_id=category.id,
            category=category.display_name,
            merchant_name=merchant_name,
            merchant_type=merchant_type,
            provider="Plaid",
            user_id=account.user_id,
            personal_finance_category=pfc or None,
            personal_finance_category_icon_url=pfc_icon,
        )
        db.session.add(new_txn)
        refresh_or_insert_plaid_metadata(tx, new_txn, plaid_acct.account_id)
        detect_internal_transfer(new_txn)


def _apply_removed(removed: List[dict]) -> int:
    """Delete transactions that Plaid indicates were removed."""
    if not removed:
        return 0
    ids = [r.get("transaction_id") for r in removed if r.get("transaction_id")]
    if not ids:
        return 0
    deleted = Transaction.query.filter(Transaction.transaction_id.in_(ids)).delete(
        synchronize_session=False
    )
    return int(deleted or 0)


def sync_account_transactions(account_id: str) -> Dict:
    """Run Plaid transactions/sync for a single account.

    - Resolves Account -> PlaidAccount to retrieve access_token and cursor
    - Paginates until has_more is False
    - Applies added/modified/removed atomically
    - Persists next_cursor
    """
    if TransactionsSyncRequest is None:
        raise RuntimeError("Plaid SDK missing TransactionsSyncRequest; upgrade SDK")

    account = Account.query.filter_by(account_id=account_id).first()
    if not account:
        raise ValueError(f"Account {account_id} not found")

    plaid_acct = PlaidAccount.query.filter_by(account_id=account_id).first()
    if not plaid_acct or not plaid_acct.access_token:
        raise ValueError(f"PlaidAccount or access_token missing for {account_id}")

    cursor = plaid_acct.sync_cursor or None
    access_token = plaid_acct.access_token

    total_added = 0
    total_modified = 0
    total_removed = 0
    next_cursor = cursor

    while True:
        req = TransactionsSyncRequest(access_token=access_token, cursor=next_cursor)
        resp = plaid_client.transactions_sync(req)
        data = resp.to_dict() if hasattr(resp, "to_dict") else dict(resp)

        added = data.get("added", [])
        modified = data.get("modified", [])
        removed = data.get("removed", [])
        next_cursor = data.get("next_cursor") or next_cursor
        has_more = bool(data.get("has_more"))

        # Atomic batch apply
        try:
            for tx in added:
                _upsert_transaction(tx, account, plaid_acct)
            for tx in modified:
                _upsert_transaction(tx, account, plaid_acct)
            total_removed += _apply_removed(removed)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"[SYNC] Failed applying batch for {account_id}: {e}")
            raise

        total_added += len(added)
        total_modified += len(modified)

        if not has_more:
            break

    # Persist final cursor
    plaid_acct.sync_cursor = next_cursor
    plaid_acct.last_refreshed = datetime.now(timezone.utc)
    db.session.commit()

    logger.info(
        f"[SYNC] account={account_id} added={total_added} modified={total_modified} removed={total_removed}"
    )
    return {
        "account_id": account_id,
        "added": total_added,
        "modified": total_modified,
        "removed": total_removed,
        "next_cursor": next_cursor,
    }
