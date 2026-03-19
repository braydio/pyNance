"""Plaid Transactions Sync service.

Implements Plaid's delta-based transactions/sync flow. Applies added/modified/
removed transactions inside a single DB transaction and persists the cursor.
"""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from app.config import logger, plaid_client
from app.extensions import db
from app.models import Account, Category, PlaidAccount, Transaction
from app.sql import transaction_rules_logic
from app.sql.account_logic import detect_internal_transfer, get_or_create_category
from app.sql.refresh_metadata import refresh_or_insert_plaid_metadata
from app.sql.sequence_utils import ensure_transactions_sequence
from app.utils.merchant_normalization import resolve_merchant

try:
    # Plaid SDK v13+ style imports
    from plaid.model.transactions_sync_request import TransactionsSyncRequest
except Exception:  # pragma: no cover - allow older SDKs
    TransactionsSyncRequest = None  # type: ignore


TRANSIENT_PLAID_ERROR_CODES = {
    "PRODUCT_NOT_READY",
    "RATE_LIMIT_EXCEEDED",
    "INSTITUTION_DOWN",
}


CREDIT_ACCOUNT_TYPES = {"credit card", "credit", "loan", "liability"}
INTEREST_DESCRIPTION_TOKENS = ("interest charge", "interest")
INTEREST_PFC_CATEGORIES = {"BANK_FEES_INTEREST"}


def _is_credit_account(account: Account) -> bool:
    """Return ``True`` when account type metadata indicates a liability account."""

    account_type = str(getattr(account, "type", "") or "").strip().lower()
    subtype = str(getattr(account, "subtype", "") or "").strip().lower()
    return account_type in CREDIT_ACCOUNT_TYPES or subtype in CREDIT_ACCOUNT_TYPES


def _is_interest_charge_transaction(tx: dict) -> bool:
    """Determine whether a transaction represents an interest charge."""

    description = str(tx.get("name") or tx.get("description") or "").strip().lower()
    if any(token in description for token in INTEREST_DESCRIPTION_TOKENS):
        return True

    pfc = tx.get("personal_finance_category") or {}
    pfc_detailed = str(pfc.get("detailed") or "").upper()
    if pfc_detailed in INTEREST_PFC_CATEGORIES:
        return True

    category_path = [str(value or "").strip().lower() for value in (tx.get("category") or [])]
    return category_path[:2] == ["bank fees", "interest"]


def _estimate_interest_apr(account: Account, tx: dict) -> float | None:
    """Estimate APR from an observed interest charge transaction.

    The estimate assumes the incoming transaction represents a monthly interest
    charge and annualizes that ratio against the approximated balance before the
    interest posted.
    """

    try:
        amount = abs(float(tx.get("amount") or 0))
    except (TypeError, ValueError):
        return None

    if amount <= 0:
        return None

    try:
        current_balance = abs(float(account.balance or 0))
    except (TypeError, ValueError):
        return None

    # For liabilities, Plaid interest is usually posted as a positive amount
    # that increases the amount owed. Back it out to approximate pre-charge balance.
    balance_before_charge = current_balance - amount
    if balance_before_charge <= 0:
        balance_before_charge = current_balance
    if balance_before_charge <= 0:
        return None

    monthly_rate = amount / balance_before_charge
    apr_percent = monthly_rate * 12 * 100
    return round(apr_percent, 4)


def _update_account_apr_from_interest_charge(account: Account, tx: dict) -> None:
    """Update account APR using interest transactions when provider APR is unavailable."""

    if not _is_credit_account(account):
        return
    if not _is_interest_charge_transaction(tx):
        return

    estimated_apr = _estimate_interest_apr(account, tx)
    if estimated_apr is None:
        return

    account.apr = estimated_apr


def _extract_plaid_error_code(error: Exception) -> Optional[str]:
    """Extract Plaid ``error_code`` from known exception payload shapes.

    Plaid client exceptions often expose ``error_code`` directly or encode
    details in a JSON ``body`` payload.
    """

    direct_code = getattr(error, "error_code", None)
    if direct_code:
        return str(direct_code)

    body = getattr(error, "body", None)
    if not body:
        return None

    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="ignore")

    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return None

    if isinstance(body, dict):
        code = body.get("error_code")
        return str(code) if code else None

    return None


def _transactions_sync_with_retry(
    req: TransactionsSyncRequest,
    *,
    account_id: str,
    item_id: Optional[str],
    max_attempts: int = 3,
    initial_backoff_seconds: float = 0.5,
):
    """Call Plaid ``transactions_sync`` with bounded retries for transient errors.

    The helper retries only known transient Plaid ``error_code`` values and
    re-raises all non-transient errors immediately.
    """

    for attempt in range(1, max_attempts + 1):
        try:
            return plaid_client.transactions_sync(req)
        except Exception as error:
            error_code = _extract_plaid_error_code(error)
            is_transient = error_code in TRANSIENT_PLAID_ERROR_CODES
            log_context = {
                "account_id": account_id,
                "item_id": item_id,
                "attempt": attempt,
                "attempt_count": attempt,
                "max_attempts": max_attempts,
                "error_code": error_code,
            }

            if not is_transient:
                logger.error(
                    "[SYNC] Plaid transactions_sync non-transient failure",
                    extra=log_context,
                )
                raise

            logger.warning(
                "[SYNC] Plaid transactions_sync transient failure",
                extra=log_context,
            )

            if attempt == max_attempts:
                raise

            time.sleep(initial_backoff_seconds * (2 ** (attempt - 1)))


def _parse_txn_date(val) -> datetime:
    if isinstance(val, datetime):
        # Ensure tz-aware in UTC
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time(), tzinfo=timezone.utc)
    # Expect YYYY-MM-DD
    try:
        d = datetime.strptime(val, "%Y-%m-%d").date()
        return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
    except Exception:
        # Fallback to now to avoid crashing sync; log upstream parse issues
        logger.warning(
            "[SYNC] Unexpected date format: %r; defaulting to now()",
            val,
        )
        return datetime.now(timezone.utc)


def _upsert_transaction(tx: dict, account: Account, plaid_acct: Optional[PlaidAccount]) -> None:
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

    category: Category = get_or_create_category(primary, detailed, pfc_primary, pfc_detailed, pfc_icon)

    # Normalize core fields
    txn_date = _parse_txn_date(tx.get("date"))
    description = tx.get("name") or tx.get("description") or "[no description]"
    merchant = resolve_merchant(
        merchant_name=tx.get("merchant_name"),
        name=tx.get("name"),
        description=tx.get("description"),
    )
    merchant_name = merchant.display_name
    tx["merchant_slug"] = merchant.merchant_slug
    merchant_type = (tx.get("payment_meta", {}) or {}).get("payment_method") or "Unknown"
    pending = bool(tx.get("pending", False))

    _update_account_apr_from_interest_charge(account, tx)

    existing = Transaction.query.filter_by(transaction_id=txn_id).first()
    if existing:
        changed = (
            existing.amount != tx.get("amount")
            or existing.date != txn_date
            or existing.description != description
            or existing.pending != pending
            or existing.category_id != category.id
            or existing.merchant_slug != tx.get("merchant_slug")
            or existing.merchant_name != merchant_name
            or existing.merchant_type != merchant_type
        )
        if changed:
            existing.amount = tx.get("amount")
            existing.date = txn_date
            existing.description = description
            existing.pending = pending
            existing.category_id = category.id
            existing.category = category.computed_display_name
            existing.category_slug = category.category_slug
            existing.category_display = category.computed_display_name
            existing.merchant_slug = tx.get("merchant_slug")
            existing.merchant_name = merchant_name
            existing.merchant_type = merchant_type
            existing.provider = "plaid"
            existing.personal_finance_category = pfc or None
            existing.personal_finance_category_icon_url = pfc_icon
        # Always refresh Plaid metadata (keeps aux fields current)
        if plaid_acct:
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
            category=category.computed_display_name,
            category_slug=category.category_slug,
            category_display=category.computed_display_name,
            merchant_slug=tx.get("merchant_slug"),
            merchant_name=merchant_name,
            merchant_type=merchant_type,
            provider="plaid",
            user_id=account.user_id,
            personal_finance_category=pfc or None,
            personal_finance_category_icon_url=pfc_icon,
        )
        db.session.add(new_txn)
        if plaid_acct:
            refresh_or_insert_plaid_metadata(tx, new_txn, plaid_acct.account_id)
        detect_internal_transfer(new_txn)


def _apply_removed(removed: List[dict]) -> int:
    """Delete transactions that Plaid indicates were removed."""
    if not removed:
        return 0
    ids = [r.get("transaction_id") for r in removed if r.get("transaction_id")]
    if not ids:
        return 0
    deleted = Transaction.query.filter(Transaction.transaction_id.in_(ids)).delete(synchronize_session=False)
    return int(deleted or 0)


def sync_account_transactions(account_id: str) -> Dict:
    """Run Plaid transactions/sync for a single account.

    - Resolves Account -> PlaidAccount to retrieve access_token and cursor
    - Paginates until has_more is False
    - Applies added/modified/removed atomically
    - Persists one item-scoped cursor update after all pages apply successfully
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

    # Build per-item account maps
    item_id = plaid_acct.item_id
    item_plaid_accts = PlaidAccount.query.filter_by(item_id=item_id).all() if item_id else [plaid_acct]
    acct_ids = [pa.account_id for pa in item_plaid_accts if pa.account_id]
    accounts = Account.query.filter(Account.account_id.in_(acct_ids)).all() if acct_ids else []
    account_map = {a.account_id: a for a in accounts}
    plaid_map = {pa.account_id: pa for pa in item_plaid_accts}

    # Choose a shared cursor if any exists
    if cursor is None:
        for pa in item_plaid_accts:
            if pa.sync_cursor:
                cursor = pa.sync_cursor
                break

    total_added = 0
    total_modified = 0
    total_removed = 0
    next_cursor = cursor
    ensure_transactions_sequence()

    while True:
        req_kwargs = {"access_token": access_token}
        if next_cursor:
            req_kwargs["cursor"] = next_cursor
        req = TransactionsSyncRequest(**req_kwargs)
        resp = _transactions_sync_with_retry(req, account_id=account_id, item_id=item_id)
        data = resp.to_dict() if hasattr(resp, "to_dict") else dict(resp)

        added = data.get("added", [])
        modified = data.get("modified", [])
        removed = data.get("removed", [])
        next_cursor = data.get("next_cursor") or next_cursor
        has_more = bool(data.get("has_more"))

        # Atomic batch apply
        try:
            for tx in added:
                _upsert_transaction(
                    tx,
                    account_map.get(tx.get("account_id")) or account,
                    plaid_map.get(tx.get("account_id")),
                )
            for tx in modified:
                _upsert_transaction(
                    tx,
                    account_map.get(tx.get("account_id")) or account,
                    plaid_map.get(tx.get("account_id")),
                )
            total_removed += _apply_removed(removed)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("[SYNC] Failed applying batch for %s: %s", account_id, e)
            raise

        total_added += len(added)
        total_modified += len(modified)

        if not has_more:
            break

    # Persist one final item-scoped cursor update only after pagination succeeds.
    # This keeps every account under the item aligned to the same sync checkpoint.
    for pa in item_plaid_accts:
        pa.sync_cursor = next_cursor
        # Use naive timestamp to match DB
        pa.last_refreshed = datetime.now()
    db.session.commit()

    logger.info(
        "[SYNC] account=%s added=%d modified=%d removed=%d",
        account_id,
        total_added,
        total_modified,
        total_removed,
    )
    return {
        "account_id": account_id,
        "added": total_added,
        "modified": total_modified,
        "removed": total_removed,
        "next_cursor": next_cursor,
    }
