"""Compatibility wrapper around the canonical recurring detector.

``RecurringDetector`` used to run its own exact-amount heuristic. It now delegates to
``recurring_candidate_service.detect_candidate_streams`` (the same engine as Forecast V2), so there
is exactly one recurrence detector. The legacy output shape is preserved for old callers.
"""

from __future__ import annotations

from dateutil.parser import parse

from app.services.recurring_candidate_service import detect_candidate_streams

LEGACY_ACCOUNT = "unscoped"


class RecurringDetector:
    """Detect recurring transactions from ``{amount, date, description}`` dictionaries.

    Amounts are taken as canonical cash deltas (``+`` inflow / ``-`` outflow). Rows may also carry
    ``account_id``, ``transaction_id``, ``pending``, ``is_internal`` and ``merchant_name``, which are
    passed through so pending and internal-transfer rows are excluded.
    """

    def __init__(self, transactions):
        """
        Args:
            transactions (List[dict]): Each dict must include 'amount', 'date', 'description'.
        """
        self.transactions = transactions

    def _adapt(self):
        rows = []
        for index, tx in enumerate(self.transactions):
            rows.append(
                {
                    "transaction_id": str(tx.get("transaction_id") or f"legacy-{index}"),
                    "account_id": str(tx.get("account_id") or LEGACY_ACCOUNT),
                    "date": parse(str(tx["date"])).date(),
                    "amount": tx["amount"],
                    "name": tx.get("description"),
                    "merchant_name": tx.get("merchant_name"),
                    "pending": bool(tx.get("pending", False)),
                    "is_internal": bool(tx.get("is_internal", False)),
                }
            )
        return rows

    def detect(self, min_occurrences=3):
        """Return likely recurring patterns in the legacy shape.

        Args:
            min_occurrences (int): Minimum number of cycles to report.

        Returns:
            List[dict]: ``amount``, ``description``, ``frequency``, ``last_seen``, ``occurrences``
            and ``account_id`` (when the input carried one).
        """
        rows = self._adapt()
        if not rows:
            return []
        accounts = [
            {"account_id": account_id, "type": "depository", "subtype": "checking", "user_id": "legacy"}
            for account_id in sorted({r["account_id"] for r in rows})
        ]
        found = detect_candidate_streams(
            rows,
            accounts,
            max(r["date"] for r in rows),
            lookback_days=800,
            options={"min_occurrences": int(min_occurrences)},
        )
        results = []
        for candidate in found["candidates"]:
            if candidate["observations"] < int(min_occurrences):
                continue
            results.append(
                {
                    "amount": float(candidate["signed_median"]),
                    "description": candidate["merchant_key"],
                    "frequency": candidate["cadence"],
                    "last_seen": candidate["last_observed"].isoformat(),
                    "occurrences": candidate["observations"],
                    "account_id": None if candidate["account_id"] == LEGACY_ACCOUNT else candidate["account_id"],
                }
            )
        return results
