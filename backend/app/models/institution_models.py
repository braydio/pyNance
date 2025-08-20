"""Institution-related models: Institution, Plaid, Teller."""

from datetime import datetime, timezone
from app.extensions import db
from .mixins import TimestampMixin


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


class PlaidAccount(db.Model, TimestampMixin):
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


class PlaidItem(db.Model, TimestampMixin):
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


class PlaidWebhookLog(db.Model, TimestampMixin):
    __tablename__ = "plaid_webhook_logs"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(128))
    webhook_type = db.Column(db.String(64))
    webhook_code = db.Column(db.String(64))
    item_id = db.Column(db.String(128))
    payload = db.Column(db.JSON, nullable=True)
    received_at = db.Column(db.DateTime, default=datetime.now(tz=timezone.utc))


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
