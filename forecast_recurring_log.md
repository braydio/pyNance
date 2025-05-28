### © 2025-05-28 19:50 UTC

Scaffolded `recurring_bridge.py` in `services/` to sync recurring detection results with the `RecurringTransaction` table.

- Uses `RecurringDetector.detect()` to extract recurring patterns  
- Calls `sql.recurring_logic.upsert_recurring(...)` to persist results  
- Placeholder structure for DB integration -- to be wired with live session and model hooks next
