# Currency Formatting Style

Transactions displayed on the dashboard use a consistent accounting style.

- Positive amounts show the standard `$xx.xx` format.
- Negative amounts are wrapped in parentheses and displayed in red.
- Formatting is handled via `formatAmount` from `src/utils/format.js` using `Intl.NumberFormat` for USD.

Example:

```js
formatAmount(42.5)   // "$42.50"
formatAmount(-20.1)  // "($20.10)"
```

Apply the `text-red-400` class to negative amounts to ensure visual emphasis.
