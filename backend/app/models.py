from datetime import datetime

from app.extensions import db


class PlaidItem(db.Model):
    """
    Stores Plaid-specific item metadata and access tokens.
    This table is kept separate from your Teller tokens.
    """

    __tablename__ = "plaid_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    item_id = db.Column(db.String(64), unique=True, nullable=False)
    access_token = db.Column(db.String(256), nullable=False)
    institution_name = db.Column(db.String(128), nullable=False)
    product = db.Column(
        db.String(32), nullable=False
    )  # e.g. "transactions" or "investments"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<PlaidItem(item_id={self.item_id}, institution={self.institution_name}, product={self.product})>"


class Account(db.Model):
    __tablename__ = "accounts"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.String(64), nullable=False)
    access_token = db.Column((db.String(256)))
    name = db.Column(db.String(128))
    type = db.Column(db.String(64))
    subtype = db.Column(db.String(64))
    status = db.Column(db.String(64))
    institution_name = db.Column(db.String(128))
    balance = db.Column(db.Float, default=0)
    last_refreshed = db.Column(db.String(64))
    link_type = db.Column(db.String(64), default="InsertProvider")

    # Set up cascading deletes for related records
    details = db.relationship(
        "AccountDetails", backref="account", uselist=False, cascade="all, delete-orphan"
    )
    history = db.relationship(
        "AccountHistory", backref="account", lazy=True, cascade="all, delete-orphan"
    )
    transactions = db.relationship(
        "Transaction", backref="account", lazy=True, cascade="all, delete-orphan"
    )


class AccountDetails(db.Model):
    __tablename__ = "account_details"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), unique=True, nullable=False
    )
    enrollment_id = db.Column(db.String(64))
    refresh_links = db.Column(db.Text)  # Stored as JSON string


class AccountHistory(db.Model):
    __tablename__ = "account_history"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    balance = db.Column(db.Float, default=0)


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(64), unique=True, nullable=False)
    account_id = db.Column(db.String(64), db.ForeignKey("accounts.account_id"))
    amount = db.Column(db.Float, default=0)
    date = db.Column(db.String(64))
    description = db.Column(db.String(256))
    category = db.Column(db.String(128), default="Unknown")
    primary_category = db.Column(db.String(128), default="Unknown")
    detailed_category = db.Column(db.String(128), default="Unknown")
    merchant_name = db.Column(db.String(128), default="Unknown")
    merchant_typ = db.Column(db.String(64), default="Unknown")
    user_modified = db.Column(db.Boolean, default=False)
    user_modified_fields = db.Column(db.Text)  # JSON representation


class RecurringTransaction(db.Model):
    __tablename__ = "recurring_transactions"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), nullable=False
    )
    description = db.Column(db.String(256), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(
        db.String(64), nullable=True
    )  # daily, weekly, monthly, yearly, etc.
    next_due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.String(256), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
