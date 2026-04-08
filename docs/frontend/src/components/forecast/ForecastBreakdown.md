# ForecastBreakdown

## Purpose

`ForecastBreakdown` lists the cashflow items that make up the forecast projection.

## Props

- `forecastItems`: Array of forecast cashflow items including `label`, `amount`, `category`,
  `source`, optional `confidence`, and optional `sources`.
- `viewType`: Current view mode (`Month` or `Year`).

## Interaction contract

- Each rendered breakdown row is a button.
- Clicking a row emits `select-item` with the selected cashflow item payload.
- `ForecastLayout` is the owner of modal state and listens for `select-item` to open the details
  modal.

## Modal detail expectations (owned by `ForecastLayout`)

When a breakdown item is selected, the layout modal shows:

- source transactions/events from `item.sources` (if present),
- category/tag and confidence context from the selected item and source references,
- provenance label indicating whether the item is from a historical average, recurring rule,
  manual adjustment, or auto-detected entry,
- empty-state copy: `No source transactions or events are attached to this forecast item.` when
  no source references are available.

## Notes

- When no items are available, the component renders an empty-state message instead of an empty list.
