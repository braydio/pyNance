import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from config import logger

logger.info("Initializing forecast stat model")


class ForecastEngine:
    def __init__(self, order=(2, 1, 2)):
        self.order = order
        self.model = None

    def fit(self, series: pd.Series):
        self.model = ARIMA(series, order=self.order).fit()
        return self

    def forecast(self, steps: int = 60):
        if not self.model:
            raise ValueError("Model not fit. Call `fit()` first.")
        forecast = self.model.forecast(steps=steps)
        return forecast.tolist()

    def evaluate(self, series: pd.Series, steps: int = 10):
        if len(series) <= steps:
            raise ValueError("Series too short for evaluation.")
        train, test = series[:-steps], series[-steps:]
        self.fit(train)
        preds = self.forecast(steps)
        mse = mean_squared_error(test, preds)
        logger.info(f"ARIMA Evaluation MSE: {mse}")
        return mse
