"""Shared mixins for SQLAlchemy models."""

from datetime import datetime
from app.extensions import db


class TimestampMixin:
    # Use naive UTC timestamps to match DB columns (no timezone=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )
