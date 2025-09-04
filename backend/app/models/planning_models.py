# backend/app/models/planning.py
# --- Planning Features

import uuid
from datetime import datetime, timezone

from app.extensions import db
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID

AllocationType = db.Enum("fixed", "percent", name="allocation_type")


class PlanningScenario(db.Model):
    __tablename__ = "planning_scenarios"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(120), nullable=False)

    created_at = db.Column(
        db.DateTime, default=datetime.now(tz=timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.now(tz=timezone.utc),
        nullable=False,
    )

    bills = db.relationship(
        "PlannedBill",
        backref="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
    allocations = db.relationship(
        "ScenarioAllocation",
        backref="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )


class PlannedBill(db.Model):
    __tablename__ = "planned_bills"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("planning_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = db.Column(db.String(120), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(80), nullable=True)
    predicted = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(
        db.DateTime, default=datetime.now(tz=timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.now(tz=timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_planned_bills_amount_nonneg"),
        Index("ix_planned_bills_scenario_due", "scenario_id", "due_date"),
    )


class ScenarioAllocation(db.Model):
    __tablename__ = "scenario_allocations"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("planning_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target = db.Column(db.String(160), nullable=False)
    kind = db.Column(AllocationType, nullable=False)
    value = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime, default=datetime.now(tz=timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now(tz=timezone.utc),
        onupdate=datetime.now(tz=timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "(kind = 'fixed' AND value >= 0) OR (kind = 'percent' AND value BETWEEN 0 AND 100)",
            name="ck_alloc_value_semantics",
        ),
        Index("ix_allocations_scenario_kind", "scenario_id", "kind"),
    )


# End of models/planning.py
