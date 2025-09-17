"""Account models: Account, AccountHistory, FinancialGoal."""

from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from .mixins import TimestampMixin


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


class FinancialGoal(db.Model, TimestampMixin):
    __tablename__ = "financial_goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True, nullable=False)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id"), index=True, nullable=False
    )
    name = db.Column(db.String(128), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(256), nullable=True)

    account = db.relationship("Account", backref="goals")


class AccountSnapshotPreference(db.Model, TimestampMixin):
    __tablename__ = "account_snapshot_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    selected_account_ids = db.Column(db.JSON, nullable=False, default=list)

    @property
    def selected_ids(self) -> list[str]:
        raw = self.selected_account_ids or []
        return list(raw)
