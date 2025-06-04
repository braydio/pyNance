# backend/app/services/ Documentation

---

## 📘 `recurring_detection.py`

````markdown
# Recurring Detection Service

## Purpose

Implements pattern recognition to automatically identify recurring transactions in user data. Uses heuristics and frequency modeling to infer regular schedules from past transaction behavior.

## Key Responsibilities

- Identify repeating transactions with fixed or semi-fixed cadence
- Generate recurrence metadata (frequency, anchor date)
- Support periodic re-evaluation of recurrence likelihood

## Primary Functions

- `detect_from_transactions(transactions)`

  - Returns a list of potential recurring patterns

- `match_against_known_patterns(transaction)`

  - Determines if a new transaction fits an existing recurring profile

- `score_recurring_confidence(transaction_group)`
  - Outputs a numeric score (0-1) based on pattern strength

## Inputs

- List of user transactions (filtered by account, merchant, or category)
- Thresholds and settings (min_count, allowable_variation, etc.)

## Outputs

- `RecurringTransaction` candidates with metadata:
  ```json
  {
    "merchant": "Netflix",
    "frequency": "monthly",
    "anchor_date": "2023-02-15",
    "confidence": 0.92
  }
  ```
````

## Internal Dependencies

- `datetime`, `collections`, `statistics`
- `models.Transaction`, `models.RecurringTransaction`
- Windowed date grouping logic

## Known Behaviors

- Uses Levenshtein or token-matching for description clustering
- Detects weekly, biweekly, monthly, and irregular patterns
- Can backfill predictions for earlier periods

## Related Docs

- [`docs/dataflow/recurring_detection.md`](../../dataflow/recurring_detection.md)
- [`docs/models/RecurringTransaction.md`](../../models/RecurringTransaction.md)

```


```
