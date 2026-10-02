"""Persistence regressions for source history, pending replacement and sync checkpoints."""

import json
import os
from copy import deepcopy
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

import pytest
from app.extensions import db
from app.models import (
    Account,
    Category,
    PlaidAccount,
    PlaidSourceEvent,
    RecurringTransaction,
    Tag,
    Transaction,
    TransactionRule,
)
from app.services import plaid_sync
from app.services.plaid_audit import record_source, source_context
from app.sql.account_logic import detect_internal_transfer, get_or_create_category, refresh_data_for_plaid_account
from flask import Flask


@pytest.fixture()
def database():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        account = Account(
            account_id="checking", user_id="owner", name="Checking", type="depository", subtype="checking"
        )
        linked = PlaidAccount(
            account_id="checking", item_id="item", access_token="not-a-real-token", product="transactions"
        )
        db.session.add_all([account, linked])
        db.session.commit()
        yield account, linked
        db.session.remove()
        db.drop_all()


def payload(txn_id="tx", **changes):
    return {
        "transaction_id": txn_id,
        "account_id": "checking",
        "date": "2026-09-01",
        "amount": 25,
        "name": "Apple",
        "merchant_name": "Apple",
        "pending": False,
        "category": ["Shops", "Digital Purchase"],
        "personal_finance_category": {
            "primary": "GENERAL_MERCHANDISE",
            "detailed": "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES",
        },
        **changes,
    }


def test_repeated_upsert_and_rule_source_preservation(database):
    account, linked = database
    db.session.add(
        TransactionRule(
            user_id="owner",
            match_criteria={"description_pattern": "Apple"},
            action={"merchant_name": "Corrected merchant"},
        )
    )
    original = payload()
    with source_context(run_id="same-run"):
        plaid_sync._upsert_transaction(original, account, linked)
        plaid_sync._upsert_transaction(original, account, linked)
    db.session.commit()
    assert Transaction.query.count() == 1
    assert PlaidSourceEvent.query.count() == 1
    txn = Transaction.query.one()
    assert txn.user_id == "owner"
    assert txn.merchant_name == "Corrected Merchant"
    assert txn.plaid_meta.raw == original
    assert PlaidSourceEvent.query.one().payload == original


def test_upsert_repairs_legacy_null_transaction_owner(database):
    account, linked = database
    plaid_sync._upsert_transaction(payload(), account, linked)
    transaction = Transaction.query.one()
    transaction.user_id = None
    db.session.flush()

    plaid_sync._upsert_transaction(payload(amount=30), account, linked)

    assert transaction.user_id == account.user_id
    assert transaction.amount == Decimal("30")


def test_same_legacy_path_different_pfc_is_stable(database):
    a = get_or_create_category("Transfer", "Third Party", "FOOD_AND_DRINK", "FOOD_AND_DRINK_COFFEE", None)
    b = get_or_create_category(
        "Transfer", "Third Party", "GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_OTHER_GENERAL_MERCHANDISE", None
    )
    assert a.id != b.id
    assert a.category_slug == "FOOD_AND_DRINK_COFFEE"
    assert Category.query.count() == 2


def test_user_edits_survive_provider_updates_and_metadata_stays_original(database):
    account, linked = database
    plaid_sync._upsert_transaction(payload(), account, linked)
    txn = Transaction.query.one()
    txn.user_modified = True
    txn.user_modified_fields = json.dumps({"merchant_name": True, "category": True, "date": True})
    txn.merchant_name = "My label"
    txn.merchant_slug = "my-label"
    txn.category = "My category"
    txn.category_display = "My category"
    txn.date = date(2026, 8, 31)
    source = payload(date="2026-09-02", amount=50)
    plaid_sync._upsert_transaction(source, account, linked)
    db.session.commit()
    assert txn.amount == Decimal("50")
    assert txn.date == date(2026, 8, 31)
    assert txn.merchant_name == "My label"
    assert txn.merchant_slug == "my-label"
    assert txn.category == "My category"
    assert txn.plaid_meta.raw == source


def test_pending_replacement_keeps_annotations_and_history(database):
    account, linked = database
    plaid_sync._upsert_transaction(payload("pending", pending=True), account, linked)
    predecessor = Transaction.query.one()
    predecessor.user_modified = True
    predecessor.user_modified_fields = json.dumps({"description": True})
    predecessor.description = "My note"
    predecessor.tags.append(Tag(name="Reviewed", user_id="owner"))
    db.session.add(
        RecurringTransaction(
            transaction_id="pending",
            account_id="checking",
            frequency="monthly",
            next_due_date=date(2026, 10, 1),
            next_instance_id="pending",
        )
    )
    plaid_sync._upsert_transaction(payload("posted", pending_transaction_id="pending"), account, linked)
    db.session.commit()
    successor = Transaction.query.one()
    assert successor.transaction_id == "posted"
    assert successor.description == "My note"
    assert successor.tags[0].name == "Reviewed"
    assert RecurringTransaction.query.one().transaction_id == "posted"
    assert RecurringTransaction.query.one().next_instance_id == "posted"
    tombstone = PlaidSourceEvent.query.filter_by(event_type="retired").one()
    assert tombstone.payload["source"]["pending"] is True
    assert tombstone.payload["local"]["description"] == "My note"


@pytest.mark.parametrize("changes", [{"date": None}, {"date": "garbage"}, {"amount": "NaN"}, {"account_id": "unknown"}])
def test_invalid_provider_rows_fail_without_fabrication(database, changes):
    with pytest.raises((ValueError, TypeError)):
        plaid_sync._upsert_transaction(payload(**changes), *database)
    db.session.rollback()
    assert Transaction.query.count() == 0


def test_id_cannot_move_to_another_account(database):
    account, linked = database
    plaid_sync._upsert_transaction(payload(), account, linked)
    db.session.add_all(
        [
            Account(account_id="other", user_id="owner", name="Other"),
            PlaidAccount(account_id="other", item_id="other-item", access_token="x", product="transactions"),
        ]
    )
    db.session.flush()
    with pytest.raises(ValueError):
        plaid_sync._upsert_transaction(
            payload(account_id="other"),
            db.session.get(Account, "other"),
            PlaidAccount.query.filter_by(account_id="other").one(),
        )
    db.session.rollback()


def test_source_log_redacts_credentials_and_is_replay_safe(database):
    with source_context(run_id="run", page_index=0):
        record_source(payload(access_token="secret", payment_meta={"password": "secret"}))
        record_source(payload(access_token="secret", payment_meta={"password": "secret"}))
    db.session.commit()
    assert PlaidSourceEvent.query.count() == 1
    source = PlaidSourceEvent.query.one()
    assert "access_token" not in source.payload
    assert "password" not in source.payload["payment_meta"]
    assert len(source.payload_sha256) == 64


def configure_sync(monkeypatch, pages):
    def call(request):
        result = pages.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(plaid_sync, "TransactionsSyncRequest", lambda **kw: kw)
    monkeypatch.setattr(plaid_sync, "plaid_client", SimpleNamespace(transactions_sync=call))


def test_sync_all_pages_and_cursor_commit_together(database, monkeypatch):
    configure_sync(
        monkeypatch,
        [
            {"added": [payload("first")], "next_cursor": "page-1", "has_more": True, "request_id": "request-1"},
            {"added": [payload("second")], "next_cursor": "page-2", "has_more": False, "request_id": "request-2"},
        ],
    )
    result = plaid_sync.sync_account_transactions("checking")
    assert result["added"] == 2
    assert Transaction.query.count() == 2
    assert database[1].sync_cursor == "page-2"
    events = PlaidSourceEvent.query.order_by(PlaidSourceEvent.page_index).all()
    assert [x.request_id for x in events] == ["request-1", "request-2"]
    assert [x.cursor_before for x in events] == [None, "page-1"]


def test_sync_invalid_second_page_rolls_back_everything(database, monkeypatch):
    configure_sync(
        monkeypatch,
        [
            {"added": [payload("first")], "next_cursor": "page-1", "has_more": True},
            {"added": [payload("bad", account_id="unknown")], "next_cursor": "page-2", "has_more": False},
        ],
    )
    with pytest.raises(ValueError):
        plaid_sync.sync_account_transactions("checking")
    assert Transaction.query.count() == 0
    assert PlaidSourceEvent.query.count() == 0
    assert database[1].sync_cursor is None


def test_sync_mutation_restarts_from_original_checkpoint(database, monkeypatch):
    error = RuntimeError("mutation")
    error.error_code = "TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION"
    configure_sync(
        monkeypatch,
        [
            {"added": [payload("discarded")], "next_cursor": "page-1", "has_more": True},
            error,
            {"added": [payload("final")], "next_cursor": "final", "has_more": False},
        ],
    )
    plaid_sync.sync_account_transactions("checking")
    assert Transaction.query.one().transaction_id == "final"
    assert PlaidSourceEvent.query.count() == 1


def test_removal_is_scoped_and_source_survives(database):
    plaid_sync._upsert_transaction(payload(), *database)
    with pytest.raises(ValueError):
        plaid_sync._apply_removed([{"transaction_id": "tx"}], {"different"})
    assert Transaction.query.count() == 1
    plaid_sync._apply_removed([{"transaction_id": "tx"}], {"checking"})
    db.session.commit()
    assert Transaction.query.count() == 0
    assert {e.event_type for e in PlaidSourceEvent.query.all()} == {"observed", "removed", "retired"}


def test_legacy_refresh_uses_same_pending_and_owner_contract(database, monkeypatch):
    from app.sql import account_logic

    source = [payload("pending", pending=True), payload("posted", pending_transaction_id="pending")]
    monkeypatch.setattr(account_logic, "get_transactions", lambda **kw: deepcopy(source))
    updated, error = refresh_data_for_plaid_account(
        "x", database[0], accounts_data=[{"account_id": "checking", "balances": {"current": 100}}]
    )
    assert error is None
    assert updated
    assert Transaction.query.one().transaction_id == "posted"
    assert Transaction.query.one().user_id == "owner"


def test_transfer_matches_weekend_payment_and_rejects_purchase(database):
    account, linked = database
    card = Account(account_id="card", user_id="owner", name="Credit", type="credit")
    db.session.add(card)
    debit = Transaction(
        transaction_id="debit",
        account_id="checking",
        user_id="owner",
        date=date(2026, 9, 7),
        amount=100,
        description="AMEX EPAYMENT",
        category_slug="LOAN_PAYMENTS_CREDIT_CARD_PAYMENT",
        pending=False,
    )
    credit = Transaction(
        transaction_id="credit",
        account_id="card",
        user_id="owner",
        date=date(2026, 9, 4),
        amount=-100,
        description="ONLINE PAYMENT - THANK YOU",
        category_slug="LOAN_PAYMENTS_CREDIT_CARD_PAYMENT",
        pending=False,
    )
    db.session.add_all([debit, credit])
    db.session.flush()
    detect_internal_transfer(debit)
    assert debit.internal_match_id == "credit"
    assert credit.internal_match_id == "debit"
    purchase = Transaction(
        transaction_id="purchase",
        account_id="card",
        date=date(2026, 9, 7),
        amount=-25,
        description="Amazon purchase",
        pending=False,
    )
    transfer = Transaction(
        transaction_id="transfer",
        account_id="checking",
        date=date(2026, 9, 7),
        amount=25,
        description="ACH transfer",
        pending=False,
    )
    db.session.add_all([purchase, transfer])
    db.session.flush()
    detect_internal_transfer(transfer)
    assert not transfer.is_internal


def test_transfer_ambiguity_and_pending_rows_are_excluded(database):
    db.session.add_all(
        [
            Account(account_id="card", user_id="owner", name="Card", type="credit"),
            Account(account_id="card2", user_id="owner", name="Card 2", type="credit"),
        ]
    )
    rows = [
        Transaction(
            transaction_id="out",
            account_id="checking",
            date=date(2026, 9, 1),
            amount=100,
            description="Payment",
            pending=False,
        ),
        Transaction(
            transaction_id="in",
            account_id="card",
            date=date(2026, 9, 1),
            amount=-100,
            description="Payment",
            pending=False,
        ),
        Transaction(
            transaction_id="in2",
            account_id="card2",
            date=date(2026, 9, 1),
            amount=-100,
            description="Payment",
            pending=False,
        ),
    ]
    db.session.add_all(rows)
    db.session.flush()
    detect_internal_transfer(rows[0])
    assert not rows[0].is_internal
    rows[2].pending = True
    db.session.flush()
    detect_internal_transfer(rows[0])
    assert rows[0].internal_match_id == "in"


def test_old_pending_replay_cannot_resurrect_after_posted(database):
    plaid_sync._upsert_transaction(payload("posted", pending_transaction_id="pending"), *database)
    plaid_sync._upsert_transaction(payload("pending", pending=True), *database)
    db.session.commit()
    assert Transaction.query.one().transaction_id == "posted"
    assert PlaidSourceEvent.query.count() == 2


def test_provider_change_revalidates_old_transfer_link(database):
    account, linked = database
    plaid_sync._upsert_transaction(payload(), account, linked)
    db.session.add(Account(account_id="savings", user_id="owner", name="Savings"))
    counterpart = Transaction(
        transaction_id="other",
        account_id="savings",
        date=date(2026, 9, 1),
        amount=-25,
        description="Transfer",
        pending=False,
        is_internal=True,
        internal_match_id="tx",
    )
    db.session.add(counterpart)
    txn = Transaction.query.filter_by(transaction_id="tx").one()
    txn.is_internal = True
    txn.internal_match_id = "other"
    plaid_sync._upsert_transaction(payload(amount=40), account, linked)
    assert not txn.is_internal
    assert not counterpart.is_internal
    assert counterpart.internal_match_id is None


def test_legacy_refresh_heals_null_transaction_owner(database, monkeypatch):
    """The shared refresh upsert repairs legacy null ownership."""
    from app.sql import account_logic

    plaid_sync._upsert_transaction(payload(), *database)
    db.session.commit()
    transaction = Transaction.query.one()
    transaction.user_id = None
    db.session.commit()
    monkeypatch.setattr(account_logic, "get_transactions", lambda **kw: [payload()])
    updated, error = refresh_data_for_plaid_account(
        "x", database[0], accounts_data=[{"account_id": "checking", "balances": {"current": 100}}]
    )
    assert error is None
    assert updated
    assert Transaction.query.one().user_id == database[0].user_id


def test_legacy_refresh_preserves_conflicting_non_null_owner(database, monkeypatch):
    """A refresh must never replace a non-null owner belonging to another user."""
    from app.sql import account_logic

    plaid_sync._upsert_transaction(payload(), *database)
    db.session.commit()
    Transaction.query.one().user_id = "other-owner"
    db.session.commit()
    monkeypatch.setattr(account_logic, "get_transactions", lambda **kw: [payload()])
    updated, error = refresh_data_for_plaid_account(
        "x", database[0], accounts_data=[{"account_id": "checking", "balances": {"current": 100}}]
    )
    assert not updated
    assert error is not None
    assert Transaction.query.one().user_id == "other-owner"
