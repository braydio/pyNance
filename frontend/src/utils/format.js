// src/utils/format.js
/**
 * Convert a numeric value into a consistent USD currency string.
 *
 * Negative values are wrapped in parentheses to match accounting
 * style. Positive values render normally. Non-numeric input falls
 * back to `$0.00`.
 *
 * @param {number|string} amount - The value to format.
 * @returns {string} Formatted currency string.
 */
export function formatAmount(amount) {
  const num = Number(amount || 0)
  if (Number.isNaN(num)) return '$0.00'

  const formatted = Math.abs(num).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })

  return num < 0 ? `(${formatted})` : formatted
}

/**
 * Return the shared polarity class for monetary values.
 *
 * Sitewide money displays use green for positive values, red for
 * negative values, and inherit the surrounding text color for zero
 * or non-numeric values. The returned classes reference theme variables
 * so components can use the same financial semantics without hardcoded
 * Tailwind palettes.
 *
 * @param {number|string|null|undefined} amount - Monetary value to classify.
 * @returns {string} CSS utility class for the value polarity.
 */
export function amountPolarityClass(amount) {
  const num = Number(amount || 0)
  if (!Number.isFinite(num) || num === 0) return 'amount-neutral'
  return num > 0 ? 'amount-positive' : 'amount-negative'
}

const FORECAST_UNAVAILABLE = 'Unavailable'

const usdFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** Return a finite number, or `null` for null, undefined, empty and non-finite input. */
function finiteOrNull(value) {
  if (value === null || value === undefined || value === '') return null
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}

/**
 * Format an unsigned forecast balance (for example cash today) as USD with grouping.
 *
 * Missing or invalid data renders `Unavailable`, never `$0.00`, so a gap is not mistaken for zero.
 * Negative balances keep a plain minus sign; the accounting-parenthesis contract of `formatAmount`
 * is deliberately unchanged.
 *
 * @param {number|string|null|undefined} value - Balance to format.
 * @returns {string} For example `$1,234.56`, `-$25.40` or `Unavailable`.
 */
export function formatForecastMoney(value) {
  const num = finiteOrNull(value)
  return num === null ? FORECAST_UNAVAILABLE : usdFormatter.format(num)
}

/**
 * Format a signed cash flow: `+$1,234.56`, `-$25.40` (true minus sign) or `$0.00`.
 *
 * @param {number|string|null|undefined} value - Signed cash effect (money in is positive).
 * @param {{ showPlus?: boolean }} [options] - Set `showPlus: false` to omit the leading plus.
 * @returns {string} Formatted amount, or `Unavailable` for missing or invalid input.
 */
export function formatSignedCashflow(value, { showPlus = true } = {}) {
  const num = finiteOrNull(value)
  if (num === null) return FORECAST_UNAVAILABLE
  const text = usdFormatter.format(Math.abs(num))
  if (num === 0 || Object.is(num, -0)) return text
  if (num < 0) return `−${text}`
  return showPlus ? `+${text}` : text
}
