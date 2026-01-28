# ForecastAdjustmentsForm

## Purpose

`ForecastAdjustmentsForm` captures manual forecast adjustments and emits them to the parent layout.

## Events

- `add-adjustment`: Emitted with `{ label, amount, frequency }` when the form is submitted.

## Notes

- The frequency selector normalizes "one-time" selections to `null` so the backend treats them as single-day adjustments.
