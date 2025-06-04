# backend/app/services Documentation

---

## 📘 `recurring_bridge.py`

```markdown
# Recurring Bridge Service

## Purpose

Acts as a middleware between the transaction ingestion layer and the recurring pattern detection module. Ensures that new transactions are evaluated for recurrence and updates the recurring transaction registry accordingly.

## Key Responsibilities

- Trigger recurring detection when new transactions are added
- Update, merge, or close existing recurring entries
- Maintain data integrity across the `RecurringTransaction` model

## Primary Functions

- `evaluate_new_transaction(transaction)`

  - Checks for similarity to existing recurring patterns

- `link_to_recurring(transaction, recurring_id)`

  - Manually or programmatically connects a transaction to a known recurring record

- `recalculate_recurring_profiles(user_id)`
  - Re-analyzes entire history to regenerate pattern matches

## Inputs

- `Transaction` object (newly ingested or modified)
- Optional override flags for forced reclassification

## Outputs

- Updated or newly created `RecurringTransaction`
- Audit logs and change metadata

## Internal Dependencies

- `recurring_detection`
- `models.Transaction`, `models.RecurringTransaction`
- Classification thresholds and frequency utilities

## Known Behaviors

- Deduplicates overlapping patterns (e.g., same day + amount + description)
- Suppresses weak detections until a threshold is met
- Triggers forecast updates if schedule changes

## Related Docs

- [`docs/dataflow/recurring_flow.md`](../../dataflow/recurring_flow.md)
- [`docs/models/RecurringTransaction.md`](../../models/RecurringTransaction.md)
```

---

Next: `recurring_detection.py`?
