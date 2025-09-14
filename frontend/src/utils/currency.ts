// frontend/src/utils/currency.ts

/**
 * Utilities for formatting and converting currency values.
 *
 * These helpers standardize the presentation of monetary amounts and
 * handle conversions using a provided exchange-rate table.
 */

/**
 * Format a numeric value as a localized currency string.
 *
 * @param value - The numeric amount to format.
 * @param currency - ISO 4217 currency code. Defaults to `USD`.
 * @param locale - BCP 47 locale string for formatting. Defaults to `en-US`.
 * @returns A localized currency string.
 */
export function formatCurrency(value: number, currency = 'USD', locale = 'en-US'): string {
  return new Intl.NumberFormat(locale, { style: 'currency', currency }).format(value)
}

/**
 * Convert an amount from one currency to another using a rate table.
 *
 * @param amount - The numeric amount to convert.
 * @param from - ISO 4217 code representing the source currency.
 * @param to - ISO 4217 code representing the target currency.
 * @param rateTable - Mapping of currency codes to their relative rates.
 * @returns The converted amount in the target currency.
 */
export function convertCurrency(
  amount: number,
  from: string,
  to: string,
  rateTable: Record<string, number>,
): number {
  return (amount / rateTable[from]) * rateTable[to]
}
