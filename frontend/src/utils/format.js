// src/utils/format.js
export function formatAmount(amount) {
    const num = parseFloat(amount);
    if (isNaN(num)) return "$0.00";
    // If negative, wrap with parentheses; otherwise, display normally.
    return num < 0 
      ? `($${Math.abs(num).toLocaleString()})`
      : `$${num.toLocaleString()}`;
  }
  