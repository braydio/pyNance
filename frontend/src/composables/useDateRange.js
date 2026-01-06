/**
 * Composable utilities for generating consistent date ranges and boundaries.
 */
import { ref } from 'vue'
import { watchDebounced } from '@vueuse/core'

export function formatDateInput(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function getMonthBounds(referenceDate) {
  const start = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), 1)
  const end = new Date(referenceDate.getFullYear(), referenceDate.getMonth() + 1, 0)
  return { start, end }
}

/**
 * Ensure start and end dates are valid and in chronological order.
 *
 * @param {{ start: string; end: string }} range - Raw date range boundaries.
 * @returns {{ start: string; end: string }} Normalized start/end pair.
 */
function normalizeRange(range) {
  const startDate = new Date(range.start)
  const endDate = new Date(range.end)

  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return range
  }

  if (startDate > endDate) {
    return {
      start: formatDateInput(endDate),
      end: formatDateInput(startDate),
    }
  }

  return {
    start: formatDateInput(startDate),
    end: formatDateInput(endDate),
  }
}

/**
 * Provide normalized date range state with debounced change notifications.
 *
 * @param {Object} options - Optional configuration for the range.
 * @param {Date} [options.initialDate] - Starting reference date.
 * @param {number} [options.debounceMs=200] - Debounce window in milliseconds.
 * @param {(range: { start: string; end: string }) => void} [options.onDebouncedChange] -
 *   Callback invoked after the debounced range updates.
 * @returns {{
 *   dateRange: import('vue').Ref<{ start: string; end: string }>;
 *   debouncedRange: import('vue').Ref<{ start: string; end: string }>;
 *   formatDateInput: typeof formatDateInput;
 *   getMonthBounds: typeof getMonthBounds;
 * }}
 */
export function useDateRange(options = {}) {
  const baseDate = options.initialDate ?? new Date()
  const { start, end } = getMonthBounds(baseDate)
  const dateRange = ref({
    start: formatDateInput(start),
    end: formatDateInput(end),
  })
  const debouncedRange = ref({ ...dateRange.value })

  const notifyChange = options.onDebouncedChange ?? (() => {})
  const debounceMs = options.debounceMs ?? 200

  watchDebounced(
    dateRange,
    () => {
      const normalized = normalizeRange(dateRange.value)
      debouncedRange.value = normalized
      notifyChange(normalized)
    },
    { deep: true, debounce: debounceMs, maxWait: debounceMs * 3 },
  )

  return {
    dateRange,
    debouncedRange,
    formatDateInput,
    getMonthBounds,
  }
}
