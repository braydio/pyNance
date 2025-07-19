"""SQLAlchemy ORM models for the pyNance backend."""

from datetime import datetime, timezone

from app.extensions import db
from sqlalchemy.ext.hybrid import hybrid_property


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
    )


# --- Institution Model ---


class Institution(db.Model, TimestampMixin):
    __tablename__ = "institutions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    provider = db.Column(db.String(64), nullable=False)
    last_refreshed = db.Column(db.DateTime, nullable=True)

    accounts = db.relationship(
        "Account", back_populates="institution", cascade="all, delete"
    )
    plaid_accounts = db.relationship(
        "PlaidAccount", back_populates="institution", cascade="all, delete"
    )
    teller_accounts = db.relationship(
        "TellerAccount", back_populates="institution", cascade="all, delete"
    )


# --- Account Model ---


class Account(db.Model, TimestampMixin):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(64), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=True)
    subtype = db.Column(db.String(64), nullable=True)
    institution_name = db.Column(db.String(128), nullable=True)
    institution_db_id = db.Column(
        db.Integer, db.ForeignKey("institutions.id"), nullable=True, index=True
    )
    status = db.Column(db.String(64), default="active")
    is_hidden = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Float, default=0)
    link_type = db.Column(db.String(64), default="manual")

    plaid_account = db.relationship(
        "PlaidAccount", backref="account", uselist=False, cascade="all, delete-orphan"
    )
    teller_account = db.relationship(
        "TellerAccount", backref="account", uselist=False, cascade="all, delete-orphan"
    )
    institution = db.relationship("Institution", back_populates="accounts")

    @hybrid_property
    def is_visible(self):
        return not self.is_hidden


# --- PlaidAccount Model ---


class PlaidAccount(db.Model, TimestampMixin):
    """Plaid-linked account with access token and sync state."""

    __tablename__ = "plaid_accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False, index=True
    )
    plaid_institution_id = db.Column(db.String(128), nullable=True)
    access_token = db.Column(db.String(256), nullable=False)
    item_id = db.Column(db.String(128), nullable=True)
    product = db.Column(db.String(64), nullable=True)
    institution_id = db.Column(db.String(128), nullable=True)
    webhook = db.Column(db.String(256), nullable=True)
    last_refreshed = db.Column(db.DateTime, nullable=True)
    institution_db_id = db.Column(
        db.Integer, db.ForeignKey("institutions.id"), nullable=True
    )
    institution = db.relationship("Institution", back_populates="plaid_accounts")
    sync_cursor = db.Column(db.String(256), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_error = db.Column(db.Text, nullable=True)


# --- PlaidItem Model ---


class PlaidItem(db.Model, TimestampMixin):
    """A linked Plaid item representing one or more accounts."""

    __tablename__ = "plaid_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True, nullable=False)
    item_id = db.Column(db.String(128), unique=True, index=True, nullable=False)
    access_token = db.Column(db.String(256), nullable=False)
    institution_name = db.Column(db.String(128), nullable=True)
    product = db.Column(db.String(64), nullable=False)
    last_refreshed = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_error = db.Column(db.Text, nullable=True)


# --- PlaidWebhookLog Model ---


class PlaidWebhookLog(db.Model, TimestampMixin):
    __tablename__ = "plaid_webhook_logs"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(128))
    webhook_type = db.Column(db.String(64))
    webhook_code = db.Column(db.String(64))
    item_id = db.Column(db.String(128))
    payload = db.Column(db.JSON, nullable=True)
    received_at = db.Column(db.DateTime, default=datetime.now(tz=timezone.utc))


# --- TellerAccount Model ---


class TellerAccount(db.Model, TimestampMixin):
    __tablename__ = "teller_accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    access_token = db.Column(db.String(256), nullable=False)
    enrollment_id = db.Column(db.String(128), nullable=True)
    teller_institution_id = db.Column(db.String(128), nullable=True)
    provider = db.Column(db.String(64), default="Teller")
    last_refreshed = db.Column(db.DateTime, nullable=True)
    institution_db_id = db.Column(
        db.Integer, db.ForeignKey("institutions.id"), nullable=True
    )
    institution = db.relationship("Institution", back_populates="teller_accounts")


# --- AccountHistory Model ---


class AccountHistory(db.Model, TimestampMixin):
    __tablename__ = "account_history"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    user_id = db.Column(db.String(64), nullable=True, index=True)
    date = db.Column(db.DateTime, nullable=False)
    balance = db.Column(db.Float, default=0)
    is_hidden = db.Column(db.Boolean, default=None)

    __table_args__ = (
        db.UniqueConstraint("account_id", "date", name="_account_date_uc"),
    )


# --- RecurringTransaction Model ---


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


# --- Category Model ---


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    plaid_category_id = db.Column(db.String(64), unique=True, nullable=True)
    primary_category = db.Column(db.String(128), default="Unknown")
    detailed_category = db.Column(db.String(128), default="Unknown")
    # New Plaid personal finance categories
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


# --- Transaction Model ---


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


# --- TransactionRule Model ---


class TransactionRule(db.Model, TimestampMixin):
    """Pattern-based rule for auto-updating transactions."""

    __tablename__ = "transaction_rules"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True)
    match_criteria = db.Column(db.JSON, nullable=False)
    action = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


# --- PlaidTransactionMeta Model ---


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

    # All Plaid fields (raw)
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


# End of models.py
