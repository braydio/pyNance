# backend/app/sql/refresh_metadata.py

from app.extensions import db
from app.models import PlaidTransactionMeta


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
    meta.authorized_date = plaid_tx.get("authorized_date")
    meta.authorized_datetime = plaid_tx.get("authorized_datetime")
    meta.category = plaid_tx.get("category")
    meta.category_id = plaid_tx.get("category_id")
    meta.check_number = plaid_tx.get("check_number")
    meta.counterparties = plaid_tx.get("counterparties")
    meta.datetime = plaid_tx.get("datetime")
    meta.iso_currency_code = plaid_tx.get("iso_currency_code")
    meta.location = plaid_tx.get("location")
    meta.logo_url = plaid_tx.get("logo_url")
    meta.merchant_entity_id = plaid_tx.get("merchant_entity_id")
    meta.payment_channel = plaid_tx.get("payment_channel")
    meta.payment_meta = plaid_tx.get("payment_meta")
    meta.pending_transaction_id = plaid_tx.get("pending_transaction_id")
    meta.transaction_code = plaid_tx.get("transaction_code")
    meta.transaction_type = plaid_tx.get("transaction_type")
    meta.unofficial_currency_code = plaid_tx.get("unofficial_currency_code")
    meta.website = plaid_tx.get("website")
    # PFC confidence, if present
    pfcat = plaid_tx.get("personal_finance_category", {})
    meta.pfc_confidence_level = pfcat.get("confidence_level") if pfcat else None

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
