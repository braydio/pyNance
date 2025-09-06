"""Base classes and legacy models for exchange adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


@dataclass(frozen=True)
class OrderSpec:
    """Legacy order specification using ``qty`` instead of ``quantity``."""

    symbol: str
    side: Literal["buy", "sell"]
    qty: float
    price: Optional[float] = None
    type: Literal["limit", "market"] = "limit"


class ExchangeAdapter:
    """Base adapter providing a consistent client interface."""

    def __init__(self, client: Any | None = None) -> None:
        self.client = client
        self.ex = client
