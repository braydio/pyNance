from datetime import datetime, timezone
from app.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
    )


class Account(db.Model, TimestampMixin):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.String(64), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=True)
    subtype = db.Column(db.String(64), nullable=True)
    institution_name = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(64), default="active")
    balance = db.Column(db.Float, default=0)
    link_type = db.Column(db.String(64), default="manual")

    plaid_account = db.relationship("PlaidAccount", backref="account", uselist=False)
    teller_account = db.relationship("TellerAccount", backref="account", uselist=False)


class PlaidAccount(db.Model, TimestampMixin):
    __tablename__ = "plaid_accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    access_token = db.Column(db.String(256), nullable=False)
    item_id = db.Column(db.String(128), nullable=True)
    institution_id = db.Column(db.String(128), nullable=True)
    webhook = db.Column(db.String(256), nullable=True)
    last_synced = db.Column(db.DateTime, nullable=True)


class TellerAccount(db.Model, TimestampMixin):
    __tablename__ = "teller_accounts"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    access_token = db.Column(db.String(256), nullable=False)
    enrollment_id = db.Column(db.String(128), nullable=True)
    institution_id = db.Column(db.String(128), nullable=True)
    provider = db.Column(db.String(64), default="Teller")
    last_synced = db.Column(db.DateTime, nullable=True)


class AccountHistory(db.Model, TimestampMixin):
    __tablename__ = "account_history"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    date = db.Column(db.DateTime, nullable=False)
    balance = db.Column(db.Float, default=0)

    __table_args__ = (
        db.UniqueConstraint("account_id", "date", name="_account_date_uc"),
    )


class RecurringTransaction(db.Model):
    __tablename__ = "recurring_transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(
        db.String(64), db.ForeignKey("transactions.transaction_id"), nullable=False
    )
    transaction = db.relationship("Transaction", backref="recurrence_rule")

    frequency = db.Column(db.String(64), nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(256), nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
    )
    next_instance_id = db.Column(db.String(64), nullable=True)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    plaid_category_id = db.Column(db.String(64), unique=True, nullable=False)
    primary_category = db.Column(db.String(128), default="Unknown")
    detailed_category = db.Column(db.String(128), default="Unknown")
    display_name = db.Column(db.String(256), default="Unknown")

    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    parent = db.relationship("Category", remote_side=[id])

    def __repr__(self):
        return f"<Category(plaid_category_id={self.plaid_category_id}, display_name={self.display_name})>"


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(64), unique=True, nullable=False)
    account_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"))
    amount = db.Column(db.Float, default=0)
    date = db.Column(db.DateTime, nullable=False)  # ✅ UPDATED
    description = db.Column(db.String(256))
    provider = db.Column(db.String(64), default="manual")
    merchant_name = db.Column(db.String(128), default="Unknown")
    merchant_type = db.Column(db.String(64), default="Unknown")
    user_modified = db.Column(db.Boolean, default=False)
    user_modified_fields = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.Column(db.String(128))

    def __repr__(self):
        return (
            f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount})>"
        )
