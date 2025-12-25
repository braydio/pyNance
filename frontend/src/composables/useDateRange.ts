/**
 * useDateRange
 *
 * Provides shared date range state with helpers for month boundaries and
 * debounced change notifications for chart consumers.
 */
import { ref, watch } from 'vue'
import { debounce } from 'lodash-es'

export type DateRange = { start: string; end: string }

export type UseDateRangeOptions = {
  /**
   * Reference date used to calculate the default month boundaries.
   */
  initialDate?: Date
  /**
   * Debounce duration in milliseconds for change notifications.
   */
  debounceMs?: number
  /**
   * Callback invoked after debounced range updates.
   */
  onDebouncedChange?: (range: DateRange) => void
}

/**
 * Format a Date instance as YYYY-MM-DD without timezone shifts.
 *
 * @param date - Date instance to format.
 * @returns Date string formatted for date inputs.
 */
export function formatDateInput(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Compute the first and last day of the month for the provided date.
 *
 * @param referenceDate - Date whose month should be used.
 * @returns Start and end dates for the month.
 */
export function getMonthBounds(referenceDate: Date): { start: Date; end: Date } {
  const start = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), 1)
  const end = new Date(referenceDate.getFullYear(), referenceDate.getMonth() + 1, 0)
  return { start, end }
}

function normalizeRange(range: DateRange): DateRange {
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
 * Manage shared date range state with debounced updates for downstream
 * consumers (e.g., chart components).
 *
 * @param options - Optional configuration for defaults and debounce timing.
 * @returns Reactive date range state and helpers.
 */
export function useDateRange(options: UseDateRangeOptions = {}) {
  const baseDate = options.initialDate ?? new Date()
  const { start, end } = getMonthBounds(baseDate)
  const dateRange = ref<DateRange>({
    start: formatDateInput(start),
    end: formatDateInput(end),
  })
  const debouncedRange = ref<DateRange>({ ...dateRange.value })

  const notifyChange = options.onDebouncedChange ?? (() => {})
  const debounceMs = options.debounceMs ?? 200

  const applyRangeUpdate = debounce(() => {
    const normalized = normalizeRange(dateRange.value)
    debouncedRange.value = normalized
    notifyChange(normalized)
  }, debounceMs)

  watch(dateRange, applyRangeUpdate, { deep: true })

  return {
    dateRange,
    debouncedRange,
    formatDateInput,
    getMonthBounds,
  }
}
