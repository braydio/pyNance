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
