"""Transaction models including categories, tags, recurring schedules, and Plaid metadata."""

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from app.extensions import db
from app.utils.category_canonical import canonical_display_for_slug
from app.utils.category_display import category_display, humanize_enum, strip_parent
from sqlalchemy.orm import validates

from .mixins import TimestampMixin


class Category(db.Model):
    """Canonical transaction category with legacy and PFC provenance fields."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    plaid_category_id = db.Column(db.String(64), unique=True, nullable=True)
    primary_category = db.Column(db.String(128), default="Unknown")
    detailed_category = db.Column(db.String(128), default="Unknown")
    pfc_primary = db.Column(db.String(64), nullable=True)
    pfc_detailed = db.Column(db.String(64), nullable=True)
    pfc_icon_url = db.Column(db.String(256), nullable=True)
    category_slug = db.Column(db.String(128), nullable=True, unique=True, index=True)
    category_display = db.Column(db.String(256), nullable=True)
    display_name = db.Column(db.String(256), default="Unknown")
    parent_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    parent = db.relationship("Category", remote_side=[id])

    __table_args__ = (
        db.UniqueConstraint(
            "primary_category", "detailed_category", name="uq_category_composite"
        ),
    )

    @property
    def display_primary(self) -> str:
        if self.pfc_primary:
            return humanize_enum(self.pfc_primary)
        return self.primary_category or "Unknown"

    @property
    def display_detailed(self) -> str | None:
        if self.pfc_detailed:
            parent = self.pfc_primary or ""
            detailed = strip_parent(self.pfc_detailed, parent)
            return humanize_enum(detailed)
        return self.detailed_category or None

    @property
    def computed_display_name(self):
        if self.category_display:
            return self.category_display
        if self.category_slug:
            return canonical_display_for_slug(self.category_slug)
        if self.pfc_primary:
            return category_display(self.pfc_primary, self.pfc_detailed)
        if self.detailed_category:
            return f"{self.primary_category} - {self.detailed_category}"
        return self.primary_category


transaction_tags = db.Table(
    "transaction_tags",
    db.Column(
        "transaction_id",
        db.String(64),
        db.ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Index("ix_transaction_tags_transaction_id", "transaction_id"),
    db.Index("ix_transaction_tags_tag_id", "tag_id"),
)


class Tag(db.Model, TimestampMixin):
    """User-defined labels for grouping transactions."""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)

    transactions = db.relationship(
        "Transaction",
        secondary=transaction_tags,
        back_populates="tags",
    )

    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_tags_user_name"),)


ProviderEnum = db.Enum("manual", "plaid", name="provider_type")


class Transaction(db.Model):
    __tablename__ = "transactions"

    """Financial transaction tied to a user-linked account.

    The composite indexes declared in ``__table_args__`` mirror the filters and
    ordering used by transaction pagination to keep retrieval predictable under
    pagination and count workloads.
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=True, index=True)
    transaction_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    account_id = db.Column(
        db.String(64), db.ForeignKey("accounts.account_id", ondelete="CASCADE")
    )
    amount = db.Column(db.Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    description = db.Column(db.String(256))
    provider = db.Column(ProviderEnum, nullable=False, server_default="manual")
    merchant_name = db.Column(db.String(128), default="Unknown")
    merchant_type = db.Column(db.String(64), default="Unknown")
    user_modified = db.Column(db.Boolean, default=False)
    user_modified_fields = db.Column(db.Text)
    updated_by_rule = db.Column(db.Boolean, default=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL")
    )
    category = db.Column(db.String(128))
    category_slug = db.Column(db.String(128), nullable=True, index=True)
    category_display = db.Column(db.String(256), nullable=True)
    personal_finance_category = db.Column(db.JSON, nullable=True)
    personal_finance_category_icon_url = db.Column(db.String, nullable=True)
    pending = db.Column(db.Boolean, default=False)
    is_internal = db.Column(db.Boolean, default=False, index=True)
    transfer_type = db.Column(db.String(32), nullable=True, index=True)
    internal_match_id = db.Column(db.String(64), nullable=True)

    plaid_meta = db.relationship(
        "PlaidTransactionMeta",
        uselist=False,
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
    tags = db.relationship(
        "Tag",
        secondary=transaction_tags,
        back_populates="transactions",
        lazy="selectin",
    )

    def __repr__(self):
        return (
            f"<Transaction(transaction_id={self.transaction_id}, amount={self.amount})>"
        )

    @property
    def internal_transfer_flag(self) -> bool:
        """Backward-compatible alias for ``is_internal`` transfer classification."""

        return bool(self.is_internal)

    @internal_transfer_flag.setter
    def internal_transfer_flag(self, value: bool) -> None:
        """Set internal transfer state via the compatibility alias."""

        self.is_internal = bool(value)

    __table_args__ = (
        db.UniqueConstraint("transaction_id"),
        db.Index(
            "ix_transactions_user_date_transaction_id_desc",
            "user_id",
            sa.text("date DESC"),
            sa.text("transaction_id DESC"),
        ),
        db.Index(
            "ix_transactions_account_date_transaction_id_desc",
            "account_id",
            sa.text("date DESC"),
            sa.text("transaction_id DESC"),
        ),
        db.Index("ix_transactions_account_date", "account_id", "date"),
    )

    @validates("provider")
    def _validate_provider(self, key, value):
        """Normalize provider to match enum values and provide a safe default.

        Ensures values are lowercase and restricted to the declared enum set.
        Fallback to "manual" for unknown values.
        """
        if value is None:
            return "manual"
        v = str(value).lower()
        return v if v in ("manual", "plaid") else "manual"


class RecurringTransaction(db.Model):
    __tablename__ = "recurring_transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(
        db.String(64),
        db.ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction = db.relationship("Transaction", backref="recurrence_rule")
    account_id = db.Column(
        db.String(64),
        db.ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frequency = db.Column(db.String(64), nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(256), nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )
    next_instance_id = db.Column(db.String(64), nullable=True)


class TransactionRule(db.Model, TimestampMixin):
    __tablename__ = "transaction_rules"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True)
    match_criteria = db.Column(db.JSON, nullable=False)
    action = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class PlaidTransactionMeta(db.Model, TimestampMixin):
    __tablename__ = "plaid_transaction_meta"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(
        db.String(64),
        db.ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    transaction = db.relationship(
        "Transaction", back_populates="plaid_meta", uselist=False
    )

    plaid_account_id = db.Column(
        db.String(64),
        db.ForeignKey("plaid_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
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
    # Full raw Plaid transaction payload (for audit/rehydration)
    raw = db.Column(db.JSON, nullable=True)

    __table_args__ = (db.UniqueConstraint("transaction_id"),)
