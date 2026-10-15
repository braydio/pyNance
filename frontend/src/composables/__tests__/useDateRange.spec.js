import { describe, it, expect } from 'vitest'
import { effectScope } from 'vue'
import { getMonthToDateRange, useDateRange } from '../useDateRange'

describe('useDateRange (unmocked)', () => {
  it('defaults to the full calendar month', () => {
    const scope = effectScope()
    const { dateRange } = scope.run(() => useDateRange({ initialDate: new Date(2024, 1, 15) }))
    expect(dateRange.value).toEqual({ start: '2024-02-01', end: '2024-02-29' })
    scope.stop()
  })

  it('honors an explicit initialRange for both the picker and debounced values', () => {
    const scope = effectScope()
    const { dateRange, debouncedRange } = scope.run(() =>
      useDateRange({ initialRange: { start: '2024-02-01', end: '2024-02-15' } }),
    )
    expect(dateRange.value).toEqual({ start: '2024-02-01', end: '2024-02-15' })
    expect(debouncedRange.value).toEqual({ start: '2024-02-01', end: '2024-02-15' })
    scope.stop()
  })

  it('builds month-to-date from local calendar parts, never the future', () => {
    expect(getMonthToDateRange(new Date(2024, 1, 15, 23, 59))).toEqual({
      start: '2024-02-01',
      end: '2024-02-15',
    })
    expect(getMonthToDateRange(new Date(2025, 0, 1))).toEqual({
      start: '2025-01-01',
      end: '2025-01-01',
    })
  })
})
