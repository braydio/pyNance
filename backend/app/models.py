from datetime import datetime

from app.extensions import db


class Account(db.Model):
    __tablename__ = "accounts"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128))
    type = db.Column(db.String(64))
    subtype = db.Column(db.String(64))
    status = db.Column(db.String(64))
    institution_name = db.Column(db.String(128))
    balance = db.Column(db.Float, default=0)
    last_refreshed = db.Column(db.DateTime, default=datetime.utcnow)
    link_type = db.Column(db.String(64), default="Teller")
    details = db.relationship("AccountDetails", backref="account", uselist=False)
    history = db.relationship("AccountHistory", backref="account", lazy=True)


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
    date = db.Column(db.String(64))  # For production, consider DateTime
    description = db.Column(db.String(256))
    category = db.Column(db.String(128), default="Unknown")
    merchant_name = db.Column(db.String(128), default="Unknown")
    merchant_typ = db.Column(db.String(64), default="Unknown")
