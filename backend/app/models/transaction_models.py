"""Transaction-related models: Transaction, Category, RecurringTransaction, Rules, PlaidTransactionMeta."""

from datetime import datetime, timezone
from app.extensions import db
from .mixins import TimestampMixin


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    plaid_category_id = db.Column(db.String(64), unique=True, nullable=True)
    primary_category = db.Column(db.String(128), default="Unknown")
    detailed_category = db.Column(db.String(128), default="Unknown")
    pfc_primary = db.Column(db.String(64), nullable=True)
    pfc_detailed = db.Column(db.String(64), nullable=True)
    pfc_icon_url = db.Column(db.String(256), nullable=True)
    display_name = db.Column(db.String(256), default="Unknown")
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    parent = db.relationship("Category", remote_side=[id])

    __table_args__ = (
        db.UniqueConstraint(
            "primary_category", "detailed_category", name="uq_category_composite"
        ),
    )

    @property
    def computed_display_name(self):
        if self.detailed_category:
            return f"{self.primary_category} > {self.detailed_category}"
        return self.primary_category


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=True, index=True)
    transaction_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    account_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"))
    amount = db.Column(db.Float, default=0)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.String(256))
    provider = db.Column(db.String(64), default="manual")
    merchant_name = db.Column(db.String(128), default="Unknown")
    merchant_type = db.Column(db.String(64), default="Unknown")
    user_modified = db.Column(db.Boolean, default=False)
    user_modified_fields = db.Column(db.Text)
    updated_by_rule = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.Column(db.String(128))
    personal_finance_category = db.Column(db.JSON, nullable=True)
    personal_finance_category_icon_url = db.Column(db.String, nullable=True)
    pending = db.Column(db.Boolean, default=False)
    is_internal = db.Column(db.Boolean, default=False, index=True)
    internal_match_id = db.Column(db.String(64), nullable=True)

    plaid_meta = db.relationship(
        "PlaidTransactionMeta",
        uselist=False,
        back_populates="transaction",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount})>"
        )

    __table_args__ = (db.UniqueConstraint("transaction_id"),)


class RecurringTransaction(db.Model):
    __tablename__ = "recurring_transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(
        db.String(64), db.ForeignKey("transactions.transaction_id"), nullable=False
    )
    transaction = db.relationship("Transaction", backref="recurrence_rule")
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False, index=True
    )
    frequency = db.Column(db.String(64), nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(256), nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
    )
    next_instance_id = db.Column(db.String(64), nullable=True)


class TransactionRule(db.Model, TimestampMixin):
    __tablename__ = "transaction_rules"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True)
    match_criteria = db.Column(db.JSON, nullable=False)
    action = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class PlaidTransactionMeta(db.Model, TimestampMixin):
    __tablename__ = "plaid_transaction_meta"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(
        db.String(64),
        db.ForeignKey("transactions.transaction_id"),
        unique=True,
        nullable=False,
    )
    transaction = db.relationship(
        "Transaction", back_populates="plaid_meta", uselist=False
    )

    plaid_account_id = db.Column(
        db.String(64), db.ForeignKey("plaid_accounts.account_id"), nullable=False
    )
    plaid_account = db.relationship("PlaidAccount", backref="transaction_meta")

    account_owner = db.Column(db.String(128), nullable=True)
    authorized_date = db.Column(db.Date, nullable=True)
    authorized_datetime = db.Column(db.DateTime, nullable=True)
    category = db.Column(db.JSON, nullable=True)
    category_id = db.Column(db.String(64), nullable=True)
    check_number = db.Column(db.String(64), nullable=True)
    counterparties = db.Column(db.JSON, nullable=True)
    datetime = db.Column(db.DateTime, nullable=True)
    iso_currency_code = db.Column(db.String(8), nullable=True)
    location = db.Column(db.JSON, nullable=True)
    logo_url = db.Column(db.String(256), nullable=True)
    merchant_entity_id = db.Column(db.String(128), nullable=True)
    payment_channel = db.Column(db.String(32), nullable=True)
    payment_meta = db.Column(db.JSON, nullable=True)
    pending_transaction_id = db.Column(db.String(64), nullable=True)
    transaction_code = db.Column(db.String(64), nullable=True)
    transaction_type = db.Column(db.String(32), nullable=True)
    unofficial_currency_code = db.Column(db.String(8), nullable=True)
    website = db.Column(db.String(256), nullable=True)
    pfc_confidence_level = db.Column(db.String(32), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    __table_args__ = (db.UniqueConstraint("transaction_id"),)
