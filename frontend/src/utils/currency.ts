// frontend/src/utils/currency.ts

/**
 * Convert a numeric dollar value into integer cents.
 *
 * @param n - The dollar amount to convert.
 * @returns The amount in cents, rounded to the nearest integer.
 */
export const toCents = (n: number | string): number =>
  Math.round(Number(n || 0) * 100);

/**
 * Convert an integer cent value into dollars.
 *
 * @param c - The value in cents.
 * @returns The value converted to dollars.
 */
export const fromCents = (c: number): number => Number(c || 0) / 100;

/**
 * Format an integer cent value for display using locale currency rules.
 *
 * @param cents - The value in cents.
 * @param locale - BCP 47 language tag, defaults to `en-US`.
 * @param currency - ISO 4217 currency code, defaults to `USD`.
 * @returns A localized currency string.
 */
export const formatCurrency = (
  cents: number,
  locale = "en-US",
  currency = "USD"
): string =>
  new Intl.NumberFormat(locale, { style: "currency", currency }).format(
    fromCents(cents)
  );
