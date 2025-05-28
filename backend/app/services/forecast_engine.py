# forecast_emgine.py
import pandas as pd
from datetime import timedelta
from collections import defaultdict


class ForecastEngine:
    def __init__(self, transaction_df: pd.DataFrame):
        self.df = transaction_df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.start_date = self.df["date"].max()

    def _extract_recurring_patterns(self, account_type: str, min_occurrences=3):
        account_df = self.df[self.df["account_type"] == account_type]
        recurring = account_df.groupby(["description", "amount"]).filter(
            lambda x: len(x) >= min_occurrences
        )
        patterns = (
            recurring.groupby(["description", "amount"])["date"]
            .apply(list)
            .reset_index()
        )
        return patterns

    def forecast(self, days_ahead=60):
        forecast = []

        for acc in self.df["account_type"].unique():
            last_date = self.df[self.df["account_type"] == acc]["date"].max()
            balance = self.df[self.df["account_type"] == acc]["amount"].sum()

            # Base forecast: keep balance flat
            for i in range(days_ahead):
                day = last_date + timedelta(days=i + 1)
                forecast.append(
                    {"date": day, "value": balance, "account_type": acc, "type": "base"}
                )

            # Add recurring items
            patterns = self._extract_recurring_patterns(acc)
            for _, row in patterns.iterrows():
                desc, amt, dates = row["description"], row["amount"], row["date"]
                if len(dates) < 2:
                    continue
                freq_days = (max(dates) - min(dates)).days // (len(dates) - 1)
                for i in range(0, days_ahead, freq_days):
                    f_date = last_date + timedelta(days=i + 1)
                    forecast.append(
                        {
                            "date": f_date,
                            "value": amt,
                            "account_type": acc,
                            "type": "recurring",
                            "description": desc,
                        }
                    )

        return pd.DataFrame(forecast).sort_values("date")


import logging
from datetime import datetime

import pandas as pd
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

logger = logging.getLogger(__name__)


class ForecastEngine:
    """
    ForecastEngine provides methods to fit an ARIMA model on historical time series data,
    forecast future values, and evaluate its performance.
    """

    def __init__(self, order=(1, 1, 1)):
        """
        Initialize the ForecastEngine with a specified ARIMA order.

        Args:
            order (tuple): The (p, d, q) order of the ARIMA model.
        """
        self.order = order
        self.model = None

    def fit(self, data: pd.Series):
        """
        Fit the ARIMA model to the provided time series data.

        Args:
            data (pd.Series): A pandas Series with datetime-indexed time series data.

        Returns:
            ForecastEngine: Returns self after fitting the model.
        """
        logger.info("Fitting ARIMA model with order %s", self.order)
        self.model = ARIMA(data, order=self.order).fit()
        return self

    def forecast(self, steps: int = 1):
        """
        Forecast future values using the fitted ARIMA model.

        Args:
            steps (int): Number of future periods to forecast.

        Returns:
            list: Forecasted values for the specified number of steps.
        """
        if self.model is None:
            raise ValueError(
                "The model is not fitted yet. Call 'fit' with appropriate data first."
            )
        forecast_values = self.model.forecast(steps=steps)
        logger.info("Forecasted %d steps into the future.", steps)
        return forecast_values.tolist()

    def evaluate(self, data: pd.Series, forecast_steps: int = 1):
        """
        Evaluate the model's performance using Mean Squared Error (MSE).

        Splits the time series data into training and testing sets; fits the model on training data,
        forecasts the next 'forecast_steps' values, and computes the MSE against test data.

        Args:
            data (pd.Series): Time series data to evaluate.
            forecast_steps (int): Number of steps to forecast for evaluation.

        Returns:
            float: The computed Mean Squared Error.
        """
        if len(data) <= forecast_steps:
            raise ValueError(
                "Insufficient data for evaluation with the given number of forecast steps."
            )

        train, test = data[:-forecast_steps], data[-forecast_steps:]
        self.fit(train)
        predictions = self.forecast(steps=forecast_steps)
        mse = mean_squared_error(test, predictions)
        logger.info("Evaluation complete. MSE: %f", mse)
        return mse


# Example usage (if running as a script, remove or adapt for production code)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Create a dummy time series data for demonstration purposes
    dates = pd.date_range(start="2020-01-01", periods=100, freq="D")
    data = pd.Series([i + (i**0.5) * 5 for i in range(100)], index=dates)

    forecast_engine = ForecastEngine(order=(2, 1, 2))
    forecast_engine.fit(data)
    future_values = forecast_engine.forecast(steps=5)
    mse = forecast_engine.evaluate(data, forecast_steps=5)

    print("Forecasted Values:", future_values)
    print("Evaluation MSE:", mse)


def forecast_balances(self, horizon_days: int = 60):
    """Forecast net balances per account using recurring transaction projections."""
    forecast_txns = self.forecast(horizon_days=horizon_days)
    balances = {}

    # Get latest balance per account
    latest_balances = (
        self.db.query(AccountHistory.account_id, AccountHistory.balance)
        .order_by(AccountHistory.account_id, AccountHistory.timestamp.desc())
        .distinct(AccountHistory.account_id)
        .all()
    )
    for acc_id, bal in latest_balances:
        balances[acc_id] = bal

    # Group forecast transactions by date
    daily_txns = defaultdict(
        lambda: defaultdict(float)
    )  # date -> account_id -> net txn
    for txn in forecast_txns:
        daily_txns[txn["date"].date()][txn["account_id"]] += txn["amount"]

    # Simulate daily balances
    output = []
    for i in range(horizon_days):
        day = (datetime.utcnow() + timedelta(days=i)).date()
        for acc_id in balances:
            delta = daily_txns[day][acc_id]
            balances[acc_id] += delta
            output.append(
                {"date": day, "account_id": acc_id, "balance": balances[acc_id]}
            )

        return output
