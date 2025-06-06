from datetime import datetime, timedelta
from collections import defaultdict


class ForecastSimulator:
    """
    Simulates future balance projections using recurring transactions.
    """

    def __init__(self, starting_balance, recurring_events):
        """
        Args:
            starting_balance (float): Current account balance.
            recurring_events (list): List of dicts with keys:
                - amount (float)
                - next_due_date (str, ISO format)
                - frequency (str: 'daily', weekly', etc)
        """
        self.starting_balance = starting_balance
        self.recurring = recurring_events
        self.freq_map = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
        }

    def project(self, days=30):
        """
        Projects balance over a number of days.
        Returns:
            List[dict]: ['{date}': 'YYYY-MM-DD', 'balance': float]
        """
        balance = self.starting_balance
        projections = []
        schedule = defaultdict(list)

        for r in self.recurring:
            freq_key = r.get("frequency", "").lower()
            freq = self.freq_map.get(freq_key, 30)
            next_date = datetime.fromisoformat(r["next_due_date"])
            for _ in range(days // freq + 1):
                if (next_date - datetime.today()).days < 0:
                    next_date += timedelta(days=freq)
                    continue
                if (next_date - datetime.today()).days > days:
                    break
                schedule[next_date.date()].append(r["amount"])
                next_date += timedelta(days=freq)

        for i in range(days):
            date = datetime.today().date() + timedelta(days=i)
            daily_tx = sum(schedule[date])
            balance += daily_tx
            projections.append({"date": date.isoformat(), "balance": round(balance, 2)})

        return projections
