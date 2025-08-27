/**
 * Utility functions for sanitizing values before logging.
 * Escapes HTML-sensitive characters to prevent log injection.
 * @param {unknown} input - The value to sanitize.
 * @returns {string} A sanitized string safe for console output.
 */
export function sanitizeForLog(input) {
  const json = typeof input === 'string' ? input : JSON.stringify(input)
  return json.replace(/</g, '\\u003C').replace(/>/g, '\\u003E').replace(/&/g, '\\u0026')
}
