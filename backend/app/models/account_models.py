"""Account models: Account, AccountHistory, FinancialGoal, and related tables."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.extensions import db
from sqlalchemy.ext.hybrid import hybrid_property

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
    balance = db.Column(db.Numeric(18, 2), nullable=False, default=Decimal("0.00"))
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
    balance = db.Column(db.Numeric(18, 2), nullable=False, default=Decimal("0.00"))
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
    target_amount = db.Column(db.Numeric(18, 2), nullable=False)
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


class AccountGroup(db.Model, TimestampMixin):
    """Persistent grouping of accounts for a specific user."""

    __tablename__ = "account_groups"

    id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid4()), unique=True
    )
    user_id = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, default="Group")
    position = db.Column(db.Integer, nullable=False, default=0)
    accent = db.Column(db.String(64), nullable=True)

    memberships = db.relationship(
        "AccountGroupMembership",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="AccountGroupMembership.position",
    )
    preference = db.relationship(
        "AccountGroupPreference", back_populates="active_group", uselist=False
    )


class AccountGroupMembership(db.Model, TimestampMixin):
    """Join table linking accounts to account groups with ordering metadata."""

    __tablename__ = "account_group_memberships"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(
        db.String(36),
        db.ForeignKey("account_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id = db.Column(
        db.String(64),
        db.ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position = db.Column(db.Integer, nullable=False, default=0)

    group = db.relationship("AccountGroup", back_populates="memberships")
    account = db.relationship(
        "Account", primaryjoin="Account.account_id == AccountGroupMembership.account_id"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "group_id", "account_id", name="uq_account_group_membership"
        ),
    )


class AccountGroupPreference(db.Model, TimestampMixin):
    """Active account group selection per user."""

    __tablename__ = "account_group_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    active_group_id = db.Column(
        db.String(36),
        db.ForeignKey("account_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    active_group = db.relationship(
        "AccountGroup", back_populates="preference", foreign_keys=[active_group_id]
    )
