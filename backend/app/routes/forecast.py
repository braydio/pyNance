from fastapi import APIRouter, Depends, Query
from sqlachemy.orm import Session
from app.services.forecast_balance import ForecastSimulator
from app.sql import get_db
from app.models import Account, RecurringTransaction
from fastapi.responses import JSONResponse
from datetime import datetime

forecast = APIRouter()

@forecast.get("/forecast")
def get_forecast(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
): 
    try:
        primary_account = db.query(Account).filter(Account.is_primary == True).first()
        if not primary_account:
            return JSONResponse(status_code=204, content={"error": "Primary account not found"})

        rec_events = []
        recs = db.query(RecurringTransaction).all()
        for r in recs:
            tx = r.transaction
            if not tx:
                continue
            rec_events.append({
                "amount": tx.amount,
                "next_due_date": r.next_due_date.isoformat(),
                "frequency": r.frequency
            })

        sim = ForecastSimulator(primary_account.current_balance, rec_events)
        result = sim.project(days=days)
        return {"status": "success", "data": result}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})