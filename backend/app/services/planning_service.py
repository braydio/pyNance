# backend/app/services/planning_service.py
from sqlalchemy.orm import joinedload
from app.models import db, PlanningScenario


def get_scenario(scenario_id):
    return (
        db.session.query(PlanningScenario)
        .options(
            joinedload(PlanningScenario.bills), joinedload(PlanningScenario.allocations)
        )
        .filter(PlanningScenario.id == scenario_id)
        .first()
    )


def validate_percent_cap(scenario: PlanningScenario) -> None:
    pct = sum(a.value for a in scenario.allocations if a.kind == "percent")
    if pct > 100:
        raise ValueError("Percent allocations exceed 100%")
