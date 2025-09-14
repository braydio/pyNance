"""Pydantic models for planning features.

Defines schema objects used by the planning API to validate and
serialize data related to bills and allocation targets. These models
mirror the SQLAlchemy models but are framework agnostic and focused on
input/output validation.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class Bill(BaseModel):  # pylint: disable=too-few-public-methods
    """Represents a planned bill within a scenario."""

    id: Optional[UUID] = Field(default=None, description="Bill identifier")
    name: str = Field(..., min_length=1, description="Human readable bill name")
    amount_cents: int = Field(..., ge=0, description="Bill amount in cents")
    due_date: Optional[date] = Field(default=None, description="Optional due date")
    category: Optional[str] = Field(default=None, description="Category label")
    predicted: bool = Field(default=False, description="Whether bill is predicted")

    @validator("name")
    def name_must_not_be_blank(cls, value: str) -> str:  # pylint: disable=no-self-argument
        """Ensure the bill name is not empty."""
        if not value.strip():
            raise ValueError("name must not be empty")
        return value


class Allocation(BaseModel):  # pylint: disable=too-few-public-methods
    """Represents an allocation target for a planning scenario."""

    id: Optional[UUID] = Field(default=None, description="Allocation identifier")
    target: str = Field(..., min_length=1, description="Allocation target label")
    kind: Literal["fixed", "percent"]
    value: int = Field(..., description="Allocation value in cents or percent")

    @validator("target")
    def target_not_blank(cls, value: str) -> str:  # pylint: disable=no-self-argument
        """Ensure the allocation target is not empty."""
        if not value.strip():
            raise ValueError("target must not be empty")
        return value

    @validator("value")
    def validate_value(cls, v: int, values: dict) -> int:  # pylint: disable=no-self-argument
        """Validate allocation value according to its kind."""
        kind = values.get("kind")
        if kind == "fixed" and v < 0:
            raise ValueError("value must be non-negative for fixed allocations")
        if kind == "percent" and not 0 <= v <= 100:
            raise ValueError("percent allocations must be between 0 and 100")
        return v
