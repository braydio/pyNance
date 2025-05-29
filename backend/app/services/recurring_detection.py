from collections import defaultdict, Counter
from datetime import datetime
from dateutil.parser import parse
from statistics import mode, StatisticsError


class RecurringDetector:
    """
    Detect recurring transactions based on amount and timing patterns.
    """

    def __init__(self, transactions):
        """
        Args:
            transactions (List[dict]): Each dict must include 'amount', 'date', 'description'.
        """
        self.transactions = transactions

    def _group_by_signature(self):
        """
        Group transactions by (amount, cleaned description signature).
        Returns:
            dict: {(amount, description_signature): List[datetime]}
        """
        groups = defaultdict(list)
        for tx in self.transactions:
            amt = round(tx["amount"], 2)
            desc = "".join(filter(str.isalnum, tx["description"].lower()))[:16]
            key = (amt, desc)
            groups[key].append(parse(tx["date"]))
        return groups

    def detect(self, min_occurrences=3):
        """
        Detect likely recurring patterns.

        Args:
            min_occurrences (int): Minimum number of occurrences to consider a transaction recurring.

        Returns:
            List[dict]: Detected recurring transaction patterns.
        """
        results = []
        grouped = self._group_by_signature()

        for (amt, desc), dates in grouped.items():
            if len(dates) < min_occurrences:
                continue
            dates.sort()
            gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
            if not gaps:
                continue

            try:
                freq = mode(gaps)
            except StatisticsError:
                freq = Counter(gaps).most_common(1)[0][0]

            frequency_str = {
                1: "daily",
                7: "weekly",
                14: "biweekly",
                30: "monthly",
            }.get(freq, f"~{freq}d")

            results.append(
                {
                    "amount": amt,
                    "description": desc,
                    "frequency": frequency_str,
                    "last_seen": max(dates).isoformat(),
                    "occurrences": len(dates),
                }
            )

        return results
