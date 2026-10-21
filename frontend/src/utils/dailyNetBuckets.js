/**
 * dailyNetBuckets.js
 *
 * Presentation-only rollup of the daily economic-net rows served by
 * `GET /api/charts/daily_net` into the bar buckets the Daily Net chart draws.
 * The backend classification stays the source of truth: this only sums rows it
 * already classified (in integer cents), it never re-classifies a transaction.
 */

const MS_PER_DAY = 86400000
const ISO_DAY = /^(\d{4})-(\d{2})-(\d{2})/

export const NET_GRANULARITY_LABELS = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
  quarterly: 'Quarterly',
}

const PRESET_GRANULARITY = {
  '7d': 'daily',
  rolling_30: 'daily',
  mtd: 'daily',
  '3m': 'weekly',
  '6m': 'weekly',
  ytd: 'monthly',
  '1y': 'monthly',
}

/** Cash-movement / review fields summed alongside the economic fields (never part of net). */
const MOVEMENT_FIELDS = [
  'transfer_in',
  'transfer_out',
  'debt_settlement',
  'investment_movement',
  'unclassified_inflows',
  'unclassified_outflows',
]

/**
 * Cash-basis fields of `row.cash_flow` (funding-account legs, dollars) summed per bucket. They
 * describe actual money moving through cash accounts and are never mixed into economic net.
 */
export const CASH_FIELDS = [
  'money_out',
  'money_in',
  'net_cash',
  'direct_payment_out',
  'debt_payment_out',
  'investment_allocation_out',
  'external_person_out',
  'unclassified_out',
  'income_in',
  'refund_in',
  'financing_in',
  'investment_in',
  'unclassified_in',
  'verified_own_transfer_out',
  'verified_own_transfer_in',
]

/** Cash value (in cents) of a daily row or bucket; supports the API's nested `cash_flow`. */
function cashCents(source, field) {
  return toCents(source?.[field] ?? source?.cash_flow?.[field])
}

/**
 * Whole UTC day number for an ISO date; DST cannot add or drop a day.
 *
 * @param {string} iso - `YYYY-MM-DD`.
 * @returns {number|null} Days since the Unix epoch, or null when unparseable.
 */
export function isoToDay(iso) {
  const match = ISO_DAY.exec(String(iso ?? ''))
  if (!match) return null
  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const ms = Date.UTC(year, month - 1, day)
  const check = new Date(ms)
  if (
    check.getUTCFullYear() !== year ||
    check.getUTCMonth() !== month - 1 ||
    check.getUTCDate() !== day
  ) {
    return null
  }
  return Math.round(ms / MS_PER_DAY)
}

/** Inverse of {@link isoToDay}. */
export function dayToIso(dayNumber) {
  const d = new Date(dayNumber * MS_PER_DAY)
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(
    d.getUTCDate(),
  ).padStart(2, '0')}`
}

function utcParts(dayNumber) {
  const d = new Date(dayNumber * MS_PER_DAY)
  return {
    year: d.getUTCFullYear(),
    month: d.getUTCMonth(),
    date: d.getUTCDate(),
    dow: d.getUTCDay(),
  }
}

function utcDay(year, month, date) {
  return Math.round(Date.UTC(year, month, date) / MS_PER_DAY)
}

/**
 * Pick the bar granularity for a chart range. Presets follow the contract table;
 * custom (or unknown) ranges scale by inclusive day count.
 *
 * @param {string} timeframe - A `CHART_RANGE_PRESETS` value or `custom`.
 * @param {string} startDate - Inclusive ISO start.
 * @param {string} endDate - Inclusive ISO end.
 * @returns {'daily'|'weekly'|'monthly'|'quarterly'}
 */
export function resolveNetGranularity(timeframe, startDate, endDate) {
  if (PRESET_GRANULARITY[timeframe]) return PRESET_GRANULARITY[timeframe]
  const start = isoToDay(startDate)
  const end = isoToDay(endDate)
  if (start == null || end == null || end < start) return 'daily'
  const days = end - start + 1
  if (days <= 45) return 'daily'
  if (days <= 210) return 'weekly'
  if (days > 1095) return 'quarterly'
  return 'monthly'
}

/** Calendar period (Monday weeks, calendar months/quarters) containing a day. */
function periodContaining(dayNumber, granularity) {
  if (granularity === 'daily') return { start: dayNumber, end: dayNumber }
  const { year, month, dow } = utcParts(dayNumber)
  if (granularity === 'weekly') {
    const start = dayNumber - ((dow + 6) % 7)
    return { start, end: start + 6 }
  }
  if (granularity === 'monthly') {
    return { start: utcDay(year, month, 1), end: utcDay(year, month + 1, 1) - 1 }
  }
  const quarterStart = month - (month % 3)
  return { start: utcDay(year, quarterStart, 1), end: utcDay(year, quarterStart + 3, 1) - 1 }
}

function toCents(value) {
  const raw = value && typeof value === 'object' ? value.parsedValue : value
  const num = Number(raw)
  return Number.isFinite(num) ? Math.round(num * 100) : 0
}

function emptyTotals() {
  const totals = { income: 0, expenses: 0, refunds: 0, net: 0, transaction_count: 0 }
  MOVEMENT_FIELDS.forEach((field) => {
    totals[field] = 0
  })
  CASH_FIELDS.forEach((field) => {
    totals[field] = 0
  })
  return totals
}

/**
 * Roll daily rows up into buckets covering exactly the inclusive `[startDate, endDate]`.
 * The first and last bucket may be partial; rows outside the selected window (for
 * example the 30-day warmup the chart fetches for moving averages) are ignored.
 *
 * @param {Array<object>} dailyRows - Rows from `daily_net` (`{date, income, expenses, net, refunds, ...}`).
 * @param {string} startDate - Inclusive ISO start.
 * @param {string} endDate - Inclusive ISO end.
 * @param {'daily'|'weekly'|'monthly'|'quarterly'} granularity
 * @returns {Array<object>} Buckets with dollar amounts rounded from integer cents.
 */
export function buildNetBuckets(dailyRows, startDate, endDate, granularity = 'daily') {
  const first = isoToDay(startDate)
  const last = isoToDay(endDate)
  if (first == null || last == null || last < first) return []

  const periods = []
  for (let cursor = first; cursor <= last; ) {
    const period = periodContaining(cursor, granularity)
    periods.push({
      periodStart: period.start,
      periodEnd: period.end,
      start: Math.max(period.start, first),
      end: Math.min(period.end, last),
      totals: emptyTotals(),
    })
    cursor = period.end + 1
  }

  let pointer = 0
  const sorted = (dailyRows || [])
    .map((row) => ({ row, day: isoToDay(row?.date) }))
    .filter((entry) => entry.day != null && entry.day >= first && entry.day <= last)
    .sort((a, b) => a.day - b.day)

  sorted.forEach(({ row, day }) => {
    while (pointer < periods.length - 1 && day > periods[pointer].end) pointer += 1
    const totals = periods[pointer].totals
    totals.income += toCents(row.income)
    totals.expenses += toCents(row.expenses)
    totals.refunds += toCents(row.refunds)
    totals.net += toCents(row.net)
    totals.transaction_count += Number(row.transaction_count) || 0
    MOVEMENT_FIELDS.forEach((field) => {
      totals[field] += toCents(row[field])
    })
    CASH_FIELDS.forEach((field) => {
      totals[field] += cashCents(row, field)
    })
  })

  return periods.map(({ periodStart, periodEnd, start, end, totals }) => {
    const startIso = dayToIso(start)
    const endIso = dayToIso(end)
    const bucket = {
      key: `${granularity}:${startIso}:${endIso}`,
      granularity,
      startDate: startIso,
      endDate: endIso,
      periodStart: dayToIso(periodStart),
      periodEnd: dayToIso(periodEnd),
      isPartial: start !== periodStart || end !== periodEnd,
      dayCount: end - start + 1,
      transaction_count: totals.transaction_count,
    }
    ;['income', 'expenses', 'refunds', 'net', ...MOVEMENT_FIELDS, ...CASH_FIELDS].forEach(
      (field) => {
        bucket[field] = totals[field] / 100
      },
    )
    return bucket
  })
}

/** Sum the fields of a bucket list (or daily rows) to cent precision. */
export function sumNetBuckets(buckets) {
  const cents = { income: 0, expenses: 0, refunds: 0, net: 0 }
  ;(buckets || []).forEach((bucket) => {
    Object.keys(cents).forEach((field) => {
      cents[field] += toCents(bucket?.[field])
    })
  })
  return {
    totalIncome: cents.income / 100,
    totalExpenses: cents.expenses / 100,
    totalRefunds: cents.refunds / 100,
    totalNet: cents.net / 100,
  }
}

/**
 * Cash-basis totals (funding accounts) for daily rows or buckets. A separate measure from
 * {@link sumNetBuckets}: it is never added to economic income, expenses or net.
 */
export function sumCashBuckets(buckets) {
  const cash = Object.fromEntries(CASH_FIELDS.map((field) => [field, 0]))
  ;(buckets || []).forEach((bucket) => {
    CASH_FIELDS.forEach((field) => {
      cash[field] += cashCents(bucket, field)
    })
  })
  return {
    totalMoneyOut: cash.money_out / 100,
    totalMoneyIn: cash.money_in / 100,
    totalNetCash: cash.net_cash / 100,
    cashBreakdown: Object.fromEntries(CASH_FIELDS.map((field) => [field, cash[field] / 100])),
  }
}

function monthName(month) {
  return new Date(Date.UTC(2000, month, 1)).toLocaleDateString('en-US', {
    month: 'short',
    timeZone: 'UTC',
  })
}

function spansYears(bucket, options) {
  return options.multiYear || bucket.startDate.slice(0, 4) !== bucket.endDate.slice(0, 4)
}

function dayLabel(iso, withYear) {
  const day = isoToDay(iso)
  if (day == null) return iso
  const { year, month, date } = utcParts(day)
  return `${monthName(month)} ${date}${withYear ? `, ${year}` : ''}`
}

/**
 * Human label for a bucket.
 *
 * @param {object} bucket - Bucket from {@link buildNetBuckets}.
 * @param {{ style?: 'tick'|'long', multiYear?: boolean }} [options] - `tick` is compact for
 *   axes; `long` carries the exact inclusive dates and year for details and screen readers.
 */
export function formatNetBucketLabel(bucket, options = {}) {
  if (!bucket) return ''
  const long = options.style === 'long'
  const withYear = long || spansYears(bucket, options)
  const start = isoToDay(bucket.startDate)
  const end = isoToDay(bucket.endDate)
  if (start == null || end == null) return bucket.startDate || ''
  const s = utcParts(start)
  const e = utcParts(end)

  if (bucket.granularity === 'daily') return dayLabel(bucket.startDate, withYear)

  if (bucket.granularity === 'weekly') {
    if (!long && !bucket.isPartial) return dayLabel(bucket.startDate, withYear)
    if (s.year !== e.year)
      return `${dayLabel(bucket.startDate, true)} – ${dayLabel(bucket.endDate, true)}`
    const range =
      s.month === e.month
        ? `${monthName(s.month)} ${s.date}–${e.date}`
        : `${monthName(s.month)} ${s.date} – ${monthName(e.month)} ${e.date}`
    return long || withYear ? `${range}, ${e.year}` : range
  }

  if (bucket.granularity === 'monthly') {
    const base = long || withYear ? `${monthName(s.month)} ${s.year}` : monthName(s.month)
    return long && bucket.isPartial
      ? `${base} (${dayLabel(bucket.startDate, false)}–${e.date})`
      : base
  }

  const quarter = `Q${Math.floor(s.month / 3) + 1} ${s.year}`
  return long && bucket.isPartial
    ? `${quarter} (${dayLabel(bucket.startDate, false)} – ${dayLabel(bucket.endDate, false)})`
    : quarter
}

/**
 * Title word for a granularity (`Daily`, `Weekly`, ...).
 */
export function netGranularityTitle(granularity) {
  return NET_GRANULARITY_LABELS[granularity] || NET_GRANULARITY_LABELS.daily
}

/**
 * Compact axis currency: `$1.2k`, `-$2.4k`, `$850`.
 */
export function formatCompactCurrency(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return '$0'
  const abs = Math.abs(num)
  const sign = num < 0 ? '-' : ''
  if (abs >= 1_000_000) return `${sign}$${trim(abs / 1_000_000)}M`
  if (abs >= 1000) return `${sign}$${trim(abs / 1000)}k`
  return `${sign}$${Math.round(abs)}`
}

function trim(value) {
  return value.toFixed(1).replace(/\.0$/, '')
}

/**
 * Prior comparison interval of an equivalent span, or null when none is defined.
 * MTD -> same days of the prior month; YTD -> prior calendar year to date; everything
 * else -> the immediately preceding interval of equal inclusive length.
 *
 * @returns {{ mode: string, start: string, end: string, label: string }|null}
 */
export function resolveComparisonInterval(timeframe, startDate, endDate) {
  const start = isoToDay(startDate)
  const end = isoToDay(endDate)
  if (start == null || end == null || end < start) return null
  const s = utcParts(start)
  const e = utcParts(end)

  if (timeframe === 'mtd') {
    const priorStart = utcDay(e.year, e.month - 1, 1)
    const priorMonthLength = utcDay(e.year, e.month, 1) - priorStart
    return {
      mode: 'prior_month_to_date',
      start: dayToIso(priorStart),
      end: dayToIso(priorStart + Math.min(e.date, priorMonthLength) - 1),
      label: 'Same days last month',
    }
  }

  if (timeframe === 'ytd') {
    const priorEndMonthLength = utcDay(e.year - 1, e.month + 1, 1) - utcDay(e.year - 1, e.month, 1)
    return {
      mode: 'prior_year_to_date',
      start: dayToIso(utcDay(s.year - 1, s.month, s.date)),
      end: dayToIso(utcDay(e.year - 1, e.month, Math.min(e.date, priorEndMonthLength))),
      label: 'Same period last year',
    }
  }

  const days = end - start + 1
  return {
    mode: 'previous_period',
    start: dayToIso(start - days),
    end: dayToIso(start - 1),
    label: 'Matching prior interval',
  }
}

/**
 * Pair each current bucket with the total net of the equivalent day span inside the
 * comparison interval (same offset from the interval start, same inclusive length).
 * A bucket whose span would run past the comparison interval gets `null` rather than a
 * fabricated zero or a delta between spans of different length.
 *
 * @param {Array<object>} priorRows - Daily rows covering the comparison interval.
 * @param {Array<object>} buckets - Current buckets from {@link buildNetBuckets}.
 * @param {string} currentStart - Inclusive ISO start of the current range.
 * @param {{ start: string, end: string }} interval - From {@link resolveComparisonInterval}.
 * @returns {Array<number|null>} Prior net per current bucket (dollars).
 */
export function buildComparisonNets(
  priorRows,
  buckets,
  currentStart,
  interval,
  basis = 'economic',
) {
  const base = isoToDay(currentStart)
  const priorStart = isoToDay(interval?.start)
  const priorEnd = isoToDay(interval?.end)
  if (base == null || priorStart == null || priorEnd == null) return (buckets || []).map(() => null)

  const netByDay = new Map()
  ;(priorRows || []).forEach((row) => {
    const day = isoToDay(row?.date)
    if (day != null) {
      const cents = basis === 'cash' ? cashCents(row, 'net_cash') : toCents(row.net)
      netByDay.set(day, (netByDay.get(day) || 0) + cents)
    }
  })

  return (buckets || []).map((bucket) => {
    const from = priorStart + (isoToDay(bucket.startDate) - base)
    const to = priorStart + (isoToDay(bucket.endDate) - base)
    if (to > priorEnd) return null
    let cents = 0
    for (let day = from; day <= to; day += 1) cents += netByDay.get(day) || 0
    return cents / 100
  })
}
