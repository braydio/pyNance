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


/** Inclusive chart date presets, shared by Dashboard and standalone chart routes. */
export const CHART_RANGE_PRESETS = [
  { value: '7d', label: '7D' },
  { value: 'rolling_30', label: '30D' },
  { value: 'mtd', label: 'MTD' },
  { value: '3m', label: '3M' },
  { value: '6m', label: '6M' },
  { value: 'ytd', label: 'YTD' },
  { value: '1y', label: '1Y' },
]

/**
 * Get a local-calendar, inclusive interval. 3M/6M/1Y are trailing calendar
 * months, clamped for month-end dates; 7D/30D are exact inclusive day counts.
 * YTD always starts January 1. Unknown keys fall back to MTD.
 */
export function getChartPresetRange(preset, now = new Date()) {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const end = formatDateInput(today)
  if (preset === 'ytd') return { start: formatDateInput(new Date(today.getFullYear(), 0, 1)), end }
  if (preset === '7d' || preset === 'rolling_30') {
    const days = preset === '7d' ? 7 : 30
    return { start: formatDateInput(new Date(today.getFullYear(), today.getMonth(), today.getDate() - days + 1)), end }
  }
  const trailingMonths = { '3m': 3, '6m': 6, '1y': 12 }[preset]
  if (trailingMonths) {
    const first = new Date(today.getFullYear(), today.getMonth() - trailingMonths, 1)
    const maxDay = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate()
    const anchor = new Date(first.getFullYear(), first.getMonth(), Math.min(today.getDate(), maxDay) + 1)
    return { start: formatDateInput(anchor), end }
  }
  return getMonthToDateRange(today)
}

export function getMonthBounds(referenceDate) {
  const start = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), 1)
  const end = new Date(referenceDate.getFullYear(), referenceDate.getMonth() + 1, 0)
  return { start, end }
}

/**
 * Month-to-date range (first of the month through `now`) as local YYYY-MM-DD strings.
 *
 * @param {Date} [now] - Reference date, defaults to the current local date.
 * @returns {{ start: string; end: string }} Inclusive range that never extends into the future.
 */
export function getMonthToDateRange(now = new Date()) {
  return {
    start: formatDateInput(new Date(now.getFullYear(), now.getMonth(), 1)),
    end: formatDateInput(now),
  }
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
 * @param {{ start: string; end: string }} [options.initialRange] - Explicit starting range;
 *   overrides the month-bounds default when supplied.
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
  const dateRange = ref(
    options.initialRange
      ? { ...options.initialRange }
      : {
          start: formatDateInput(start),
          end: formatDateInput(end),
        },
  )
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
