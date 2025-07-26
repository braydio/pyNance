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
  const num = Number(amount || 0);
  if (Number.isNaN(num)) return '$0.00';

  const formatted = Math.abs(num).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return num < 0 ? `(${formatted})` : formatted;
}
