# Currency Formatting Style

Transactions displayed on the dashboard use a consistent accounting style.

- Positive amounts show the standard `$xx.xx` format.
- Negative amounts are wrapped in parentheses and displayed in red.
- Formatting is handled via `formatAmount` from `src/utils/format.js` using
  `Intl.NumberFormat` for USD.

Example:

```js
formatAmount(42.5); // "$42.50"
formatAmount(-20.1); // "($20.10)"
```

Use `amountPolarityClass` from `src/utils/format.js` for sitewide amount color semantics. It returns `amount-positive`, `amount-negative`, or `amount-neutral`, which map through theme variables to green, red, or inherited text color. Apply the helper anywhere a signed money value is rendered so dashboard detail views, trend deltas, outlier amounts, tables, and summary panels stay consistent.
