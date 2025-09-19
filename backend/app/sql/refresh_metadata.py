# backend/app/sql/refresh_metadata.py

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.extensions import db
from app.models import PlaidTransactionMeta


def _coerce_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    if isinstance(value, str):
        cleaned = value.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(cleaned)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _sanitize_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def refresh_or_insert_plaid_metadata(
    plaid_tx: dict, transaction, plaid_account_id: str
):
    """
    Insert or update the PlaidTransactionMeta for a given Transaction.
    Args:
        plaid_tx: The Plaid transaction dictionary (raw response).
        transaction: The Transaction SQLAlchemy instance (already created/updated).
        plaid_account_id: The PlaidAccount.account_id (for FK).
    """
    meta = PlaidTransactionMeta.query.filter_by(
        transaction_id=transaction.transaction_id
    ).first()
    if not meta:
        meta = PlaidTransactionMeta(transaction_id=transaction.transaction_id)
        db.session.add(meta)

    # Always set required relationships
    meta.transaction = transaction
    meta.plaid_account_id = plaid_account_id

    # Plaid-specific fields
    meta.account_owner = plaid_tx.get("account_owner")
    meta.authorized_date = _coerce_date(plaid_tx.get("authorized_date"))
    meta.authorized_datetime = _coerce_datetime(
        plaid_tx.get("authorized_datetime")
    )
    meta.category = _sanitize_for_json(plaid_tx.get("category"))
    meta.category_id = plaid_tx.get("category_id")
    meta.check_number = plaid_tx.get("check_number")
    meta.counterparties = _sanitize_for_json(plaid_tx.get("counterparties"))
    meta.datetime = _coerce_datetime(plaid_tx.get("datetime"))
    meta.iso_currency_code = plaid_tx.get("iso_currency_code")
    meta.location = _sanitize_for_json(plaid_tx.get("location"))
    meta.logo_url = plaid_tx.get("logo_url")
    meta.merchant_entity_id = plaid_tx.get("merchant_entity_id")
    meta.payment_channel = plaid_tx.get("payment_channel")
    meta.payment_meta = _sanitize_for_json(plaid_tx.get("payment_meta"))
    meta.pending_transaction_id = plaid_tx.get("pending_transaction_id")
    meta.transaction_code = plaid_tx.get("transaction_code")
    meta.transaction_type = plaid_tx.get("transaction_type")
    meta.unofficial_currency_code = plaid_tx.get("unofficial_currency_code")
    meta.website = plaid_tx.get("website")
    # PFC confidence, if present
    pfcat = plaid_tx.get("personal_finance_category", {})
    meta.pfc_confidence_level = pfcat.get("confidence_level") if pfcat else None

    # Store full raw payload for audit/debug/rehydration
    meta.raw = _sanitize_for_json(plaid_tx)

    # Mark as active
    meta.is_active = True

    # You can extend with custom logic (eg. handle custom JSON dumps, defaults, etc.)

    return meta  # (Not committing, caller should commit the session)


def batch_refresh_plaid_metadata(plaid_tx_list, transaction_map, plaid_account_id):
    """
    Utility to upsert PlaidTransactionMeta for a batch of transactions.
    Args:
        plaid_tx_list: List of Plaid transaction dicts.
        transaction_map: Dict mapping Plaid transaction_id -> Transaction SQLA object.
        plaid_account_id: FK for the related PlaidAccount.
    """
    metas = []
    for tx in plaid_tx_list:
        txn_id = tx.get("transaction_id")
        transaction = transaction_map.get(txn_id)
        if transaction:
            meta = refresh_or_insert_plaid_metadata(tx, transaction, plaid_account_id)
            metas.append(meta)
    return metas
