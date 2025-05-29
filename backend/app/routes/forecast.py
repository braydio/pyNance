
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.services.forecast.forecast_balance import ForecastSimulator
from backend.app.sql import models, database
from datetime import date

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


@router.get("/balance")
def get_balance_projection(days: int = 30, db: Session = Depends(database.get_db)):
    # 1. Fetch current balance (use first account as example for now)
    account = db.query(models.Account).first()
    starting_balance = account.current_balance if account else 0.0

    # 2. Load recurring tx from DB
    recs = db.query(models.RecurringTransaction).all()
    recurring_events = [
      {
            "amount": r.amount,
            "frequency": r.frequency,
            "next_due_date": r.next_due_date.isoformat(),
        }
      for r in recs
    ]

    # 3. Run simulation
    simulator = ForecastSimulator(starting_balance, recurring_events)
    forecast = simulator.project(days=days)
    return forecast