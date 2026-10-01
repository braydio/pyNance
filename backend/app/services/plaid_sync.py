"""Plaid Transactions Sync service.

Implements Plaid's delta-based transactions/sync flow. Applies added/modified/
removed transactions inside a single DB transaction and persists the cursor.
"""

from __future__ import annotations

import json
import time
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import uuid4

from app.config import logger, plaid_client
from app.extensions import db
from app.models import Account, Category, PlaidAccount, Transaction
from app.services.plaid_audit import (
    clear_transfer,
    ingestion_lock,
    modified_fields,
    record_source,
    retire_transaction,
    source_context,
)
from app.sql import transaction_rules_logic
from app.sql.account_logic import detect_internal_transfer, get_or_create_category
from app.sql.dialect_utils import dialect_insert
from app.sql.refresh_metadata import refresh_or_insert_plaid_metadata
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


def _parse_txn_date(val) -> date:
    """Return Plaid's transaction calendar date without adding a timezone."""

    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if not isinstance(val, str):
        raise ValueError("Plaid date must be a calendar date")
    return datetime.strptime(val, "%Y-%m-%d").date()


def _upsert_transaction(tx: dict, account: Account, plaid_acct: Optional[PlaidAccount]) -> str:
    """Persist original source, then project rules without overwriting user edits."""
    original = deepcopy(tx)
    txn_id = tx.get("transaction_id")
    if not txn_id or tx.get("account_id") != account.account_id or not plaid_acct:
        raise ValueError("Plaid transaction identity/account is missing or unrecognized")
    if plaid_acct.account_id != account.account_id:
        raise ValueError("Plaid metadata account does not match local account")
    if not account.user_id:
        raise ValueError("Linked Plaid account owner is required")
    ingestion_lock("plaid-owner:" + account.user_id)
    # Item locks protect checkpoints; identity locks cover duplicate IDs across items.
    ingestion_lock("plaid-transaction:" + txn_id)
    txn_date = _parse_txn_date(tx.get("date"))
    amount = Decimal(str(tx.get("amount")))
    if not amount.is_finite():
        raise ValueError("Plaid amount must be finite")
    record_source(original, account_id=account.account_id, item_id=plaid_acct.item_id)
    if original.get("pending"):
        from app.models import PlaidTransactionMeta

        successors = (
            Transaction.query.join(
                PlaidTransactionMeta, Transaction.transaction_id == PlaidTransactionMeta.transaction_id
            )
            .filter(
                PlaidTransactionMeta.pending_transaction_id == txn_id,
                Transaction.account_id == account.account_id,
                Transaction.pending.is_(False),
            )
            .all()
        )
        if len(successors) > 1:
            raise ValueError("Pending transaction has multiple posted successors")
        if successors:
            predecessor = Transaction.query.filter_by(transaction_id=txn_id).first()
            if predecessor:
                retire_transaction(predecessor, reason="pending_replaced", successor=successors[0])
                return "updated"
            return "unchanged"
    tx = transaction_rules_logic.apply_rules(account.user_id, deepcopy(tx))
    txn_date = _parse_txn_date(tx.get("date"))
    amount = Decimal(str(tx.get("amount")))
    if not amount.is_finite():
        raise ValueError("Rule transaction amount must be finite")
    pfc = tx.get("personal_finance_category") or {}
    legacy_path = tx.get("category") or []
    if not isinstance(legacy_path, (list, tuple)):
        legacy_path = []
    category = None
    if tx.get("category_id"):
        category = db.session.get(Category, tx["category_id"])
    if not category:
        category = get_or_create_category(
            legacy_path[0] if legacy_path else "Unknown",
            legacy_path[1] if len(legacy_path) > 1 else "Unknown",
            pfc.get("primary"),
            pfc.get("detailed"),
            tx.get("personal_finance_category_icon_url"),
        )
    merchant = resolve_merchant(
        merchant_name=tx.get("merchant_name"), name=tx.get("name"), description=tx.get("description")
    )
    values = dict(
        transaction_id=txn_id,
        account_id=account.account_id,
        user_id=account.user_id,
        provider="plaid",
        amount=amount,
        date=txn_date,
        description=tx.get("description") or tx.get("name") or "[no description]",
        pending=bool(tx.get("pending", False)),
        category_id=category.id,
        category=category.computed_display_name,
        category_slug=category.category_slug,
        category_display=category.computed_display_name,
        merchant_name=merchant.display_name,
        merchant_slug=merchant.merchant_slug,
        merchant_type=(tx.get("payment_meta") or {}).get("payment_method") or "Unknown",
        personal_finance_category=pfc or None,
        personal_finance_category_icon_url=tx.get("personal_finance_category_icon_url"),
        updated_by_rule=bool(tx.get("updated_by_rule", False)),
    )
    existing = Transaction.query.filter_by(transaction_id=txn_id).first()
    inserted = existing is None
    if not existing:
        stmt = dialect_insert(Transaction.__table__).values(**values)
        db.session.execute(stmt.on_conflict_do_nothing(index_elements=["transaction_id"]))
        existing = Transaction.query.filter_by(transaction_id=txn_id).populate_existing().one()
    if existing.account_id != account.account_id or existing.provider != "plaid":
        raise ValueError("Provider transaction ID conflicts with another account/provider")
    if existing.user_id and existing.user_id != account.user_id:
        raise ValueError("Provider transaction owner conflicts with linked account")
    protected = modified_fields(existing)
    if protected & {"category", "category_id", "category_slug", "category_display"}:
        protected |= {"category", "category_id", "category_slug", "category_display"}
    if "merchant_name" in protected:
        protected.add("merchant_slug")
    changed = False
    if any(
        getattr(existing, key) != values[key]
        for key in ("amount", "date", "pending", "description", "merchant_name", "category_slug")
        if key not in protected
    ):
        clear_transfer(existing)
    for key, value in values.items():
        if key not in protected and getattr(existing, key) != value:
            setattr(existing, key, value)
            changed = True
    refresh_or_insert_plaid_metadata(original, existing, plaid_acct.account_id)
    pending_id = original.get("pending_transaction_id")
    if pending_id and not original.get("pending") and pending_id != txn_id:
        predecessor = Transaction.query.filter_by(transaction_id=pending_id).first()
        if predecessor:
            retire_transaction(predecessor, reason="pending_replaced", successor=existing)
            changed = True
    db.session.flush()
    detect_internal_transfer(existing)
    _update_account_apr_from_interest_charge(account, original)
    return "inserted" if inserted else "updated" if changed else "unchanged"


def _apply_removed(removed: List[dict], allowed_accounts: set[str]) -> int:
    """Scope removal to the current item and retain tombstones and local state."""
    count = 0
    for source in removed:
        txn_id = source.get("transaction_id")
        if not txn_id:
            raise ValueError("Plaid removal is missing transaction_id")
        transaction = Transaction.query.filter_by(transaction_id=txn_id).first()
        if transaction and (transaction.account_id not in allowed_accounts or transaction.provider != "plaid"):
            raise ValueError("Plaid removal conflicts with a different item/provider")
        record_source(source, event_type="removed")
        if transaction:
            retire_transaction(transaction, reason="provider_removed")
            count += 1
    return count


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

    item_id = plaid_acct.item_id
    # Lock before re-reading any cursors; all ingestion paths use the same key.
    ingestion_lock("plaid-owner:" + str(account.user_id))
    ingestion_lock("plaid-item:" + (item_id or account_id))
    db.session.refresh(plaid_acct)
    access_token = plaid_acct.access_token
    item_plaid_accts = (
        PlaidAccount.query.filter_by(item_id=item_id).populate_existing().all() if item_id else [plaid_acct]
    )
    acct_ids = [pa.account_id for pa in item_plaid_accts]
    accounts = Account.query.filter(Account.account_id.in_(acct_ids)).all()
    account_map = {a.account_id: a for a in accounts}
    plaid_map = {pa.account_id: pa for pa in item_plaid_accts}
    cursors = {pa.sync_cursor for pa in item_plaid_accts if pa.sync_cursor}
    if len(cursors) > 1:
        db.session.rollback()
        raise ValueError("Plaid item has inconsistent sync checkpoints")
    initial_cursor = next(iter(cursors), None)
    run_id = str(uuid4())
    # Fetch every page before projecting any of it; mutation restarts use the
    # original checkpoint and never leave partially committed provider state.
    try:
        for attempt in range(3):
            pages = []
            next_cursor = initial_cursor
            try:
                while True:
                    kwargs = {"access_token": access_token}
                    if next_cursor:
                        kwargs["cursor"] = next_cursor
                    resp = _transactions_sync_with_retry(
                        TransactionsSyncRequest(**kwargs), account_id=account_id, item_id=item_id
                    )
                    data = resp.to_dict() if hasattr(resp, "to_dict") else dict(resp)
                    cursor_after = data.get("next_cursor")
                    if not cursor_after or (data.get("has_more") and cursor_after == next_cursor):
                        raise ValueError("Plaid sync returned a missing or non-progressing cursor")
                    pages.append((next_cursor, data))
                    next_cursor = cursor_after
                    if not data.get("has_more"):
                        break
                break
            except Exception as error:
                if _extract_plaid_error_code(error) != "TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION" or attempt == 2:
                    raise
        totals = {"added": 0, "modified": 0, "removed": 0}
        for page_index, (cursor_before, data) in enumerate(pages):
            with source_context(
                run_id=run_id,
                page_index=page_index,
                item_id=item_id,
                endpoint="transactions/sync",
                request_id=data.get("request_id"),
                cursor_before=cursor_before,
                cursor_after=data["next_cursor"],
            ):
                for event_type in ("added", "modified"):
                    with source_context(event_type=event_type):
                        for tx in data.get(event_type, []):
                            target = account_map.get(tx.get("account_id"))
                            if not target or target.user_id != account.user_id:
                                raise ValueError("Plaid sync returned an unknown account or owner")
                            _upsert_transaction(tx, target, plaid_map.get(tx.get("account_id")))
                            totals[event_type] += 1
                totals["removed"] += _apply_removed(data.get("removed", []), set(acct_ids))
        for pa in item_plaid_accts:
            pa.sync_cursor = next_cursor
            pa.last_refreshed = datetime.now(timezone.utc)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.error("[SYNC] Item sync rolled back for account=%s", account_id)
        raise
    from app.sql.account_logic import invalidate_tx_cache

    invalidate_tx_cache()
    logger.info(
        "[SYNC] account=%s added=%d modified=%d removed=%d",
        account_id,
        totals["added"],
        totals["modified"],
        totals["removed"],
    )
    return {"account_id": account_id, **totals, "next_cursor": next_cursor}
