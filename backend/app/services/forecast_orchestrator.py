from .forecast_engine import ForecastEngine as ForecastEngineRuleBased
from .forecast_stat_model import ForecastEngine as ForecastEngineStatModel


class ForecastOrchestrator:
    def __init__(self, db):
        self.db = db
        self.rule_engine = ForecastEngineRuleBased(db)
        self.stat_engine = ForecastEngineStatModel()

    def forecast(self, method="rule", days=60):
        if method == "rule":
            return self.rule_engine.forecast_balances(horizon_days=days)
        elif method == "stat":
            return self.stat_engine.forecast(days)
        else:
            raise ValueError("Unknown forecast method: choose 'rule' or 'stat'")
