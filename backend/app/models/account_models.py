"""Account domain models including link metadata, history snapshots, and goals."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.extensions import db
from sqlalchemy.ext.hybrid import hybrid_property

from .mixins import TimestampMixin

# Database enums
AccountStatusEnum = db.Enum(
    "active", "inactive", "closed", "archived", name="account_status"
)
LinkTypeEnum = db.Enum("manual", "plaid", name="link_type")


class Account(db.Model, TimestampMixin):
    __tablename__ = "accounts"

    # Use business key as the primary key across the schema
    account_id = db.Column(db.String(64), primary_key=True, nullable=False, index=True)
    user_id = db.Column(db.String(64), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(64), nullable=True)
    subtype = db.Column(db.String(64), nullable=True)
    # Denormalized display value; prefer joining institutions.name where possible
    institution_name = db.Column(db.String(128), nullable=True)
    institution_db_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    status = db.Column(AccountStatusEnum, nullable=False, server_default="active")
    is_hidden = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    link_type = db.Column(LinkTypeEnum, nullable=False, server_default="manual")

    plaid_account = db.relationship(
        "PlaidAccount", backref="account", uselist=False, cascade="all, delete-orphan"
    )
    institution = db.relationship("Institution", back_populates="accounts")

    @staticmethod
    def _normalize_display_segment(value: str | None) -> str | None:
        """Normalize a display-name segment and drop unknown placeholders."""

        cleaned = (value or "").strip()
        if not cleaned:
            return None
        if cleaned.lower() in {
            "unknown",
            "unknown institution",
            "unknown account type",
        }:
            return None
        return cleaned

    @staticmethod
    def _format_account_type(
        subtype: str | None, account_type: str | None
    ) -> str | None:
        """Return a title-cased account type label from subtype or type values."""

        source = Account._normalize_display_segment(
            subtype
        ) or Account._normalize_display_segment(account_type)
        if not source:
            return None
        return source.replace("_", " ").replace("-", " ").title()

    def format_display_name(
        self, mask: str | None = None, last4: str | None = None
    ) -> str:
        """Build a canonical display name from institution/type metadata and optional mask.

        Args:
            mask: Optional account mask value supplied by external providers.
            last4: Optional final four digits when ``mask`` is unavailable.

        Returns:
            Canonical account label that prefers institution and subtype/type metadata,
            appending a masked suffix when available. Falls back to raw ``name``.
        """

        institution = self._normalize_display_segment(self.institution_name)
        account_type = self._format_account_type(self.subtype, self.type)
        suffix = (mask or last4 or "").strip()

        parts = [part for part in (institution, account_type) if part]
        label = " • ".join(parts)
        if suffix:
            masked = f"•••• {suffix}"
            return f"{label} • {masked}" if label else masked
        if label:
            return label
        return (self.name or "Unnamed Account").strip() or "Unnamed Account"

    @property
    def display_name(self) -> str:
        """Return the canonical account label for API presentation."""

        return self.format_display_name()

    @hybrid_property
    def is_visible(self):
        return not self.is_hidden


class AccountHistory(db.Model, TimestampMixin):
    __tablename__ = "account_history"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(
        db.String(64),
        db.ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(db.String(64), nullable=True, index=True)
    # Daily snapshots; store as a Date (UTC day)
    date = db.Column(db.Date, nullable=False)
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
        db.String(64),
        db.ForeignKey("accounts.account_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
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
