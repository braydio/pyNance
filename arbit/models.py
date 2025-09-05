"""Core data models for exchange interactions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


@dataclass(frozen=True)
class Triangle:
    """Represents a triangular arbitrage opportunity."""

    leg_ab: str
    leg_bc: str
    leg_ac: str


@dataclass(frozen=True)
class OrderSpec:
    """Specification for placing an order on an exchange."""

    symbol: str
    side: Literal["buy", "sell"]
    quantity: float
    price: Optional[float] = None
    order_type: Literal["limit", "market"] = "limit"


@dataclass(frozen=True)
class Fill:
    """Execution details of a completed order."""

    order_id: str
    symbol: str
    side: Literal["buy", "sell"]
    price: float
    quantity: float
    fee: float
    timestamp: datetime | None = None

    def __getitem__(self, key: str):
        """Provide dict-style access for backward compatibility."""
        if key == "qty":
            return self.quantity
        return getattr(self, key)
