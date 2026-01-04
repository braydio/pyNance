
// Composable utility to generate consistent date ranges and boundaries.
import { ref, watch } from 'vue'
import { debounce } from 'lodash-es'

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
