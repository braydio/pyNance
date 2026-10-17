import { describe, expect, it } from 'vitest'
import { getChartPresetRange, CHART_RANGE_PRESETS } from './useDateRange'

const at = (yyyy, mm, dd) => new Date(yyyy, mm - 1, dd)

describe('chart range presets (inclusive local calendar)', () => {
  it('offers consistent dashboard and expanded-view timeframes', () => {
    expect(CHART_RANGE_PRESETS.map((item) => item.value)).toEqual(
      ['7d', 'rolling_30', 'mtd', '3m', '6m', 'ytd', '1y'],
    )
  })
  it('supports short, rolling-quarter, half-year, YTD and trailing-year ranges', () => {
    const today = at(2026, 10, 17)
    expect(getChartPresetRange('7d', today)).toEqual({ start: '2026-10-11', end: '2026-10-17' })
    expect(getChartPresetRange('rolling_30', today)).toEqual({ start: '2026-09-18', end: '2026-10-17' })
    expect(getChartPresetRange('mtd', today)).toEqual({ start: '2026-10-01', end: '2026-10-17' })
    expect(getChartPresetRange('3m', today)).toEqual({ start: '2026-07-18', end: '2026-10-17' })
    expect(getChartPresetRange('6m', today)).toEqual({ start: '2026-04-18', end: '2026-10-17' })
    expect(getChartPresetRange('ytd', today)).toEqual({ start: '2026-01-01', end: '2026-10-17' })
    expect(getChartPresetRange('1y', today)).toEqual({ start: '2025-10-18', end: '2026-10-17' })
  })
  it('clamps month ends without UTC shift or future-dating', () => {
    expect(getChartPresetRange('3m', at(2026, 5, 31))).toEqual({ start: '2026-03-01', end: '2026-05-31' })
    expect(getChartPresetRange('1y', at(2024, 2, 29))).toEqual({ start: '2023-03-01', end: '2024-02-29' })
    expect(getChartPresetRange('ytd', at(2026, 1, 1))).toEqual({ start: '2026-01-01', end: '2026-01-01' })
  })
})
