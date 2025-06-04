# 📘 `RecurringTransaction` Model

```markdown
# RecurringTransaction Model

## Purpose

Tracks inferred or manually identified recurring transaction patterns. Supports predictions, budgeting, and forecast alignment for expected future financial activity.

## Fields

- `id`: Primary key (UUID)
- `user_id`: FK to the owner of the pattern
- `description`: Canonical label for the recurring item
- `anchor_date`: Most recent known occurrence date
- `frequency`: Enum or string (`monthly`, `weekly`, `biweekly`, `irregular`, etc.)
- `estimated_amount`: Average or most recent transaction amount
- `category_id`: Optional FK to `Category`
- `active`: Boolean — whether pattern is still expected
- `confidence_score`: Float (0.0–1.0) from pattern detection
- `source`: `auto` | `manual`
- `created_at`, `updated_at`: Audit timestamps

## Relationships

- One-to-many with `Transaction` (linked by heuristic or admin override)
- Belongs to `User`, optionally assigned `Category`

## Behaviors

- Automatically refreshed by recurring detection engine
- Can be edited by users if confidence is below a threshold
- Forecasting uses this model to inject expected future items

## Related Logic

- [`recurring_detection.py`](../../backend/app/services/recurring_detection.py)
- [`recurring_logic.py`](../../backend/app/db_logic/recurring_logic.py)
- [`forecast_engine.py`](../../backend/app/services/forecast_engine.py)

## Related Docs

- [`docs/dataflow/recurring_detection.md`](../../docs/dataflow/recurring_detection.md)
- [`docs/sql/RecurringQueryPatterns.md`](../../docs/sql/RecurringQueryPatterns.md)
```
