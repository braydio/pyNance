import { describe, it, expect } from 'vitest'
import { CHART_RANGE_PRESETS, getChartPresetRange } from '@/composables/useDateRange'
import {
  resolveNetGranularity,
  buildNetBuckets,
  formatNetBucketLabel,
  formatCompactCurrency,
  resolveComparisonInterval,
  buildComparisonNets,
  sumNetBuckets,
  sumCashBuckets,
  isoToDay,
  dayToIso,
} from '../dailyNetBuckets'

const NOW = new Date(2026, 9, 19) // Mon 2026-10-19

const money = (v) => ({ source: String(v), parsedValue: v })
const row = (date, income, expenses, refunds = 0, extra = {}) => ({
  date,
  income: money(income),
  expenses: money(expenses),
  refunds,
  net: money(Math.round((income + expenses + refunds) * 100) / 100),
  transaction_count: 1,
  ...extra,
})

function bucketsFor(preset) {
  const { start, end } = getChartPresetRange(preset, NOW)
  const granularity = resolveNetGranularity(preset, start, end)
  return { start, end, granularity, buckets: buildNetBuckets([], start, end, granularity) }
}

describe('resolveNetGranularity / preset bucket counts (frozen 2026-10-19)', () => {
  it.each([
    ['7d', 'daily', 7],
    ['rolling_30', 'daily', 30],
    ['mtd', 'daily', 19],
  ])('%s -> %s x%i', (preset, granularity, count) => {
    const result = bucketsFor(preset)
    expect(result.granularity).toBe(granularity)
    expect(result.buckets).toHaveLength(count)
  })

  it('uses Monday-anchored weekly buckets for 3M and 6M', () => {
    for (const [preset, min, max] of [
      ['3m', 13, 15],
      ['6m', 26, 28],
    ]) {
      const { buckets, granularity } = bucketsFor(preset)
      expect(granularity).toBe('weekly')
      expect(buckets.length).toBeGreaterThanOrEqual(min)
      expect(buckets.length).toBeLessThanOrEqual(max)
      buckets.forEach((b) => {
        expect(new Date(`${b.periodStart}T00:00:00Z`).getUTCDay()).toBe(1)
      })
    }
  })

  it('YTD is exactly ten month buckets Jan-Oct with a partial October', () => {
    const { buckets, granularity } = bucketsFor('ytd')
    expect(granularity).toBe('monthly')
    expect(buckets).toHaveLength(10)
    expect(buckets[0].startDate).toBe('2026-01-01')
    expect(buckets[9]).toMatchObject({
      startDate: '2026-10-01',
      endDate: '2026-10-19',
      isPartial: true,
    })
    expect(buckets[8].isPartial).toBe(false)
  })

  it('1Y is monthly with partial start and end', () => {
    const { buckets, granularity } = bucketsFor('1y')
    expect(granularity).toBe('monthly')
    expect(buckets.length).toBeGreaterThanOrEqual(12)
    expect(buckets.length).toBeLessThanOrEqual(13)
    expect(buckets.at(-1).isPartial).toBe(true)
  })

  it('never emits daily buckets for YTD or 1Y', () => {
    ;['ytd', '1y'].forEach((p) => expect(bucketsFor(p).granularity).not.toBe('daily'))
  })

  it('covers every preset in CHART_RANGE_PRESETS', () => {
    CHART_RANGE_PRESETS.forEach(({ value }) =>
      expect(bucketsFor(value).buckets.length).toBeGreaterThan(0),
    )
  })

  it('scales custom ranges by inclusive day count', () => {
    const g = (days) =>
      resolveNetGranularity('custom', '2026-01-01', dayToIso(isoToDay('2026-01-01') + days - 1))
    expect(g(40)).toBe('daily')
    expect(g(45)).toBe('daily')
    expect(g(46)).toBe('weekly')
    expect(g(90)).toBe('weekly')
    expect(g(210)).toBe('weekly')
    expect(g(211)).toBe('monthly')
    expect(g(300)).toBe('monthly')
    expect(g(1095)).toBe('monthly')
    expect(g(1200)).toBe('quarterly')
  })
})

describe('buildNetBuckets edges', () => {
  it('clips a week crossing Sept/Oct to its inclusive bounds as one Monday bucket', () => {
    const buckets = buildNetBuckets([], '2026-09-30', '2026-10-06', 'weekly')
    expect(buckets.map((b) => [b.startDate, b.endDate, b.periodStart])).toEqual([
      ['2026-09-30', '2026-10-04', '2026-09-28'],
      ['2026-10-05', '2026-10-06', '2026-10-05'],
    ])
    expect(buckets[0].isPartial).toBe(true)
  })

  it('handles leap day, year end and month ends', () => {
    const feb = buildNetBuckets([], '2028-02-01', '2028-03-01', 'monthly')
    expect(feb.map((b) => b.dayCount)).toEqual([29, 1])
    const year = buildNetBuckets([], '2025-12-31', '2026-01-01', 'monthly')
    expect(year.map((b) => b.startDate)).toEqual(['2025-12-31', '2026-01-01'])
    const quarters = buildNetBuckets([], '2026-02-10', '2026-08-01', 'quarterly')
    expect(quarters.map((b) => [b.startDate, b.endDate])).toEqual([
      ['2026-02-10', '2026-03-31'],
      ['2026-04-01', '2026-06-30'],
      ['2026-07-01', '2026-08-01'],
    ])
  })

  it('is DST-safe across the March spring-forward weekend', () => {
    const days = buildNetBuckets([], '2026-03-06', '2026-03-12', 'daily').map((b) => b.startDate)
    expect(days).toEqual([
      '2026-03-06',
      '2026-03-07',
      '2026-03-08',
      '2026-03-09',
      '2026-03-10',
      '2026-03-11',
      '2026-03-12',
    ])
  })

  it('does not extend past the selected end into future days', () => {
    const buckets = buildNetBuckets([], '2026-10-01', '2026-10-19', 'monthly')
    expect(buckets).toHaveLength(1)
    expect(buckets[0].endDate).toBe('2026-10-19')
  })

  it('ignores warmup rows outside the selected window and guards bad values', () => {
    const rows = [
      row('2026-09-20', 999, -1),
      row('2026-10-02', 100, -40),
      row('2026-10-03', Number.NaN, -10),
    ]
    const [bucket] = buildNetBuckets(rows, '2026-10-01', '2026-10-19', 'monthly')
    expect(bucket.income).toBe(100)
    expect(bucket.expenses).toBe(-50)
    expect(bucket.transaction_count).toBe(2)
  })

  it('returns [] for invalid or inverted ranges', () => {
    expect(buildNetBuckets([], 'x', '2026-01-01', 'daily')).toEqual([])
    expect(buildNetBuckets([], '2026-02-01', '2026-01-01', 'daily')).toEqual([])
  })
})

describe('economic reconciliation', () => {
  // $1,000 payroll, -$300 expense, +$25 refund; transfers/settlement/unclassified are movement only.
  const rows = [
    row('2026-10-05', 1000, -300, 25, {
      transfer_in: 200,
      transfer_out: 0,
      debt_settlement: 131.64,
      unclassified_inflows: 100,
    }),
  ]

  it.each(['daily', 'weekly', 'monthly', 'quarterly'])(
    '%s rollup nets +725 without movement',
    (granularity) => {
      const buckets = buildNetBuckets(rows, '2026-10-01', '2026-10-19', granularity)
      const active = buckets.find((b) => b.net !== 0)
      expect(active).toMatchObject({ income: 1000, expenses: -300, refunds: 25, net: 725 })
      expect(Math.round((active.income + active.expenses + active.refunds) * 100)).toBe(
        Math.round(active.net * 100),
      )
      expect(active.transfer_in).toBe(200)
      expect(active.debt_settlement).toBe(131.64)
      expect(active.unclassified_inflows).toBe(100)
      expect(sumNetBuckets(buckets)).toEqual({
        totalIncome: 1000,
        totalExpenses: -300,
        totalRefunds: 25,
        totalNet: 725,
      })
    },
  )

  it('keeps totals equal to raw daily sums to the cent for every preset', () => {
    const daily = []
    for (let d = isoToDay('2026-01-01'); d <= isoToDay('2026-10-19'); d += 1) {
      daily.push(
        row(dayToIso(d), 10.1 + (d % 7) / 10, -3.3 - (d % 5) / 10, d % 11 === 0 ? 1.07 : 0),
      )
    }
    CHART_RANGE_PRESETS.forEach(({ value }) => {
      const { start, end, granularity } = bucketsFor(value)
      const inWindow = daily.filter((r) => r.date >= start && r.date <= end)
      const expected = sumNetBuckets(buildNetBuckets(inWindow, start, end, 'daily'))
      expect(sumNetBuckets(buildNetBuckets(daily, start, end, granularity))).toEqual(expected)
    })
  })
})

describe('labels', () => {
  it('shows actual inclusive dates for partial buckets and years in long form', () => {
    const [sept, oct] = buildNetBuckets([], '2026-09-30', '2026-10-06', 'weekly')
    expect(formatNetBucketLabel(sept, { style: 'long' })).toBe('Sep 30 – Oct 4, 2026')
    expect(formatNetBucketLabel(oct, { style: 'long' })).toBe('Oct 5–6, 2026')
    const [jan] = buildNetBuckets([], '2026-01-01', '2026-10-19', 'monthly')
    expect(formatNetBucketLabel(jan)).toBe('Jan')
    expect(formatNetBucketLabel(jan, { multiYear: true })).toBe('Jan 2026')
    const last = buildNetBuckets([], '2026-01-01', '2026-10-19', 'monthly').at(-1)
    expect(formatNetBucketLabel(last, { style: 'long' })).toBe('Oct 2026 (Oct 1–19)')
  })

  it('disambiguates years on ticks that span years', () => {
    const [dec] = buildNetBuckets([], '2025-12-01', '2026-02-01', 'monthly')
    expect(formatNetBucketLabel(dec, { multiYear: true })).toBe('Dec 2025')
    const [q] = buildNetBuckets([], '2025-01-01', '2025-03-31', 'quarterly')
    expect(formatNetBucketLabel(q)).toBe('Q1 2025')
  })

  it('formats compact axis currency', () => {
    expect(formatCompactCurrency(1200)).toBe('$1.2k')
    expect(formatCompactCurrency(-2400)).toBe('-$2.4k')
    expect(formatCompactCurrency(850)).toBe('$850')
    expect(formatCompactCurrency(Number.NaN)).toBe('$0')
  })
})

describe('comparison intervals', () => {
  it('MTD compares the same days of the prior month, clamped', () => {
    expect(resolveComparisonInterval('mtd', '2026-03-01', '2026-03-31')).toMatchObject({
      start: '2026-02-01',
      end: '2026-02-28',
    })
  })

  it('YTD compares the prior calendar year to date', () => {
    expect(resolveComparisonInterval('ytd', '2026-01-01', '2026-10-19')).toMatchObject({
      mode: 'prior_year_to_date',
      start: '2025-01-01',
      end: '2025-10-19',
    })
  })

  it('other modes use the immediately preceding equal-length interval', () => {
    expect(resolveComparisonInterval('rolling_30', '2026-09-20', '2026-10-19')).toMatchObject({
      start: '2026-08-21',
      end: '2026-09-19',
    })
  })

  it('pairs buckets by matching day span and returns null rather than fabricating', () => {
    const buckets = buildNetBuckets([], '2026-01-01', '2026-03-31', 'monthly')
    const interval = resolveComparisonInterval('custom', '2026-01-01', '2026-03-31')
    const prior = [row('2025-10-03', 50, -20), row('2025-11-15', 10, 0)]
    expect(buildComparisonNets(prior, buckets, '2026-01-01', interval)).toEqual([30, 10, 0])
    const longer = buildNetBuckets([], '2026-01-01', '2026-04-10', 'monthly')
    expect(buildComparisonNets(prior, longer, '2026-01-01', interval).at(-1)).toBeNull()
  })

  it('marks buckets beyond the prior interval unavailable', () => {
    const buckets = buildNetBuckets([], '2026-03-01', '2026-03-31', 'daily')
    const interval = resolveComparisonInterval('mtd', '2026-03-01', '2026-03-31')
    const nets = buildComparisonNets([row('2026-02-03', 10, -2)], buckets, '2026-03-01', interval)
    expect(nets[2]).toBe(8)
    expect(nets[29]).toBeNull()
    expect(nets[30]).toBeNull()
  })
})

describe('cash-basis buckets', () => {
  const cashRow = (date, out, inn, debt = 0) => ({
    ...row(date, 0, 0),
    cash_flow: {
      money_out: out,
      money_in: inn,
      net_cash: Math.round((inn - out) * 100) / 100,
      debt_payment_out: debt,
    },
  })

  it('sums cash fields per bucket without touching economic fields', () => {
    const rows = [cashRow('2026-10-13', 600, 0, 600), cashRow('2026-10-14', 40, 1000)]
    const [bucket] = buildNetBuckets(rows, '2026-10-13', '2026-10-14', 'weekly')
    expect(bucket.money_out).toBe(640)
    expect(bucket.money_in).toBe(1000)
    expect(bucket.net_cash).toBe(360)
    expect(bucket.debt_payment_out).toBe(600)
    expect(bucket.net).toBe(0)
  })

  it('totals cash rows separately from the economic totals', () => {
    const rows = [cashRow('2026-10-13', 600, 0, 600), cashRow('2026-10-14', 40, 1000)]
    expect(sumNetBuckets(rows)).toEqual({
      totalIncome: 0,
      totalExpenses: 0,
      totalRefunds: 0,
      totalNet: 0,
    })
    const cash = sumCashBuckets(rows)
    expect(cash.totalMoneyOut).toBe(640)
    expect(cash.totalNetCash).toBe(360)
    expect(cash.cashBreakdown.debt_payment_out).toBe(600)
  })

  it('treats rows without cash_flow as zero, not as errors', () => {
    expect(sumCashBuckets([row('2026-10-13', 10, -2)]).totalMoneyOut).toBe(0)
  })

  it('builds the cash comparison series from net_cash', () => {
    const buckets = buildNetBuckets([], '2026-03-01', '2026-03-03', 'daily')
    const interval = resolveComparisonInterval('mtd', '2026-03-01', '2026-03-31')
    const nets = buildComparisonNets(
      [cashRow('2026-02-01', 30, 100)],
      buckets,
      '2026-03-01',
      interval,
      'cash',
    )
    expect(nets[0]).toBe(70)
  })
})
