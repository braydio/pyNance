# forecast_orchestrator.py
from .forecast_engine import ForecastEngine as ForecastEngineRuleBased

try:  # Optional dependency
    from .forecast_stat_model import ForecastEngine as ForecastEngineStatModel
except Exception:  # pragma: no cover - allow missing heavy deps
    ForecastEngineStatModel = None


class ForecastOrchestrator:
    def __init__(self, db):
        self.db = db
        self.rule_engine = ForecastEngineRuleBased(db)
        self.stat_engine = ForecastEngineStatModel() if ForecastEngineStatModel else None

    def forecast(self, method="rule", days=60, stat_input=None):
        if method == "rule":
            return self.rule_engine.forecast_balances(horizon_days=days)
        elif method == "stat":
            if self.stat_engine is None:
                raise ImportError("Statistical forecast engine not available")
            if stat_input is None:
                raise ValueError(
                    "Statistical forecast requires a time series input (pd.Series)."
                )
            self.stat_engine.fit(stat_input)
            return self.stat_engine.forecast(steps=days)
        else:
            raise ValueError("Unknown forecast method: choose 'rule' or 'stat'")
