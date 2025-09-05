"""Adapter implementation using the `ccxt` library."""

from __future__ import annotations

from typing import Any

from arbit.config import settings
from arbit.models import Fill, OrderSpec

from .base import ExchangeAdapter

try:  # pragma: no cover - used only when ``ccxt`` is missing
    import ccxt  # type: ignore
except ImportError:  # pragma: no cover - graceful fallback for linting
    ccxt = None


class CCXTAdapter(ExchangeAdapter):
    """Adapter for exchanges supported by the `ccxt` library."""

    def __init__(self, exchange: str, api_key: str, api_secret: str) -> None:
        if ccxt is None:  # pragma: no cover - will be skipped in tests
            raise RuntimeError("ccxt library is required")
        client = getattr(ccxt, exchange)({"apiKey": api_key, "secret": api_secret})
        super().__init__(client)
        self._fee: dict[str, tuple[float, float]] = {}

    # Basic exchange API wrappers -------------------------------------------------------------
    def fetch_orderbook(self, symbol: str, depth: int = 10) -> dict:
        """Retrieve the order book for ``symbol`` up to ``depth`` levels."""

        return self.ex.fetch_order_book(symbol, depth)

    # Compatibility wrappers expected by tests -------------------------------------------------
    def fetch_order_book(self, symbol: str, depth: int = 10) -> dict:
        """Alias for :meth:`fetch_orderbook` using snake-case name."""

        return self.fetch_orderbook(symbol, depth)

    def fetch_fees(self, symbol: str) -> tuple[float, float]:
        """Return ``(maker, taker)`` fees for ``symbol``, caching results."""

        if symbol in self._fee:
            return self._fee[symbol]
        m = self.ex.market(symbol)
        maker = m.get("maker", self.ex.fees.get("trading", {}).get("maker", 0.001))
        taker = m.get("taker", self.ex.fees.get("trading", {}).get("taker", 0.001))
        self._fee[symbol] = (maker, taker)
        return maker, taker

    def min_notional(self, symbol: str) -> float:
        """Return exchange-imposed minimum notional for ``symbol``."""

        m = self.ex.market(symbol)
        return float(m.get("limits", {}).get("cost", {}).get("min", 1.0))

    def create_order(self, spec: OrderSpec) -> Fill:
        """Place an order described by ``spec`` and return a :class:`Fill`."""

        qty = getattr(spec, "qty", None)
        if qty is None:
            qty = getattr(spec, "quantity")

        order_type = getattr(spec, "type", None)
        if order_type is None:
            order_type = getattr(spec, "order_type", "market")

        if settings.dry_run:
            ob = self.fetch_orderbook(spec.symbol, 1)
            price = ob["asks"][0][0] if spec.side == "buy" else ob["bids"][0][0]
            fee = self.fetch_fees(spec.symbol)[1] * price * qty
            return Fill(
                order_id="dryrun",
                symbol=spec.symbol,
                side=spec.side,
                price=price,
                quantity=qty,
                fee=fee,
            )

        price = getattr(spec, "price", None)
        o = self.client.create_order(spec.symbol, order_type, spec.side, qty, price)
        filled = float(o.get("filled", qty))
        price = float(o.get("average") or o.get("price") or 0.0)
        fee_cost = sum(float(f.get("cost") or 0) for f in o.get("fees", []))
        return Fill(
            order_id=o["id"],
            symbol=spec.symbol,
            side=spec.side,
            price=price,
            quantity=filled,
            fee=fee_cost,
        )

    def balances(self) -> dict[str, float]:
        """Return assets with non-zero balances."""

        b = self.ex.fetch_balance()
        return {k: float(v) for k, v in b.get("total", {}).items() if float(v or 0) > 0}

    # Additional convenience methods expected by tests ----------------------------------------
    def cancel_order(self, order_id: str, symbol: str) -> None:
        """Cancel order ``order_id`` for ``symbol`` on the exchange."""

        self.ex.cancel_order(order_id, symbol)

    def fetch_balance(self, asset: str) -> float:
        """Return free balance for ``asset``."""

        b = self.ex.fetch_balance()
        return float(b.get("free", {}).get(asset, 0.0))
