<template>
  <div class="daily-net-chart">
    <div v-if="$slots.title || $slots.controls" class="daily-net-chart__header">
      <div v-if="$slots.title" class="daily-net-chart__title-shell">
        <slot
          name="title"
          :granularity="granularity"
          :granularity-title="granularityTitle"
          :is-drilled="isDrilled"
        />
      </div>
      <div v-if="$slots.controls" class="daily-net-chart__controls-shell">
        <slot name="controls" :granularity="granularity" :granularity-title="granularityTitle" />
      </div>
    </div>

    <div v-if="hasError" class="daily-net-chart__state daily-net-chart__state--error">
      <p>Unable to load daily net data right now. Please try again.</p>
      <button class="daily-net-chart__retry" type="button" @click="retryFetch">Retry</button>
    </div>

    <div v-else-if="isLoading" class="daily-net-chart__state">Loading daily net chart…</div>

    <div v-else-if="isEmpty" class="daily-net-chart__state" data-testid="daily-net-empty">
      No activity in this period
    </div>

    <template v-else>
      <ul class="daily-net-chart__legend" aria-label="Chart legend" data-testid="daily-net-legend">
        <li
          v-for="item in baseLegend"
          :key="item.label"
          class="daily-net-chart__legend-item daily-net-chart__legend-item--base"
        >
          <span
            class="daily-net-chart__swatch"
            :class="`daily-net-chart__swatch--${item.kind}`"
            :style="{ '--legend-color': item.color }"
            aria-hidden="true"
          />
          <span class="daily-net-chart__legend-label">{{ item.label }}</span>
        </li>
      </ul>
      <ul
        v-if="legendItems.length"
        class="daily-net-chart__legend daily-net-chart__legend--overlays"
        aria-label="Active chart overlays"
      >
        <li
          v-for="item in legendItems"
          :key="item.label"
          class="daily-net-chart__legend-item angular-chart-chip"
          :style="{ '--legend-color': item.color }"
        >
          <span class="daily-net-chart__swatch daily-net-chart__swatch--dashed" aria-hidden="true" />
          <span class="daily-net-chart__legend-label">{{ item.label }}</span>
        </li>
      </ul>
      <p v-if="comparisonError" class="daily-net-chart__notice" role="status">
        Comparison data is unavailable for the matching prior interval.
      </p>

      <section
        v-if="activeDetails"
        class="daily-net-chart__details angular-chart-zone"
        aria-live="polite"
        aria-label="Active period details"
      >
        <div class="daily-net-chart__details-header">
          <p class="daily-net-chart__details-date">
            {{ activeDetails.date }}
            <span v-if="activeDetails.isPartial" class="daily-net-chart__details-partial">
              partial period
            </span>
          </p>
          <p
            class="daily-net-chart__details-net"
            :class="activeDetails.net < 0 ? 'is-negative' : 'is-positive'"
          >
            Economic Net: {{ formatAmount(activeDetails.net) }}
          </p>
        </div>
        <dl class="daily-net-chart__details-metrics">
          <div>
            <dt>Income</dt>
            <dd>{{ formatAmount(activeDetails.income) }}</dd>
          </div>
          <div>
            <dt>Expenses</dt>
            <dd>{{ formatAmount(activeDetails.expenses) }}</dd>
          </div>
          <div>
            <dt>Refunds</dt>
            <dd>{{ formatAmount(activeDetails.refunds) }}</dd>
          </div>
          <div>
            <dt>Transactions</dt>
            <dd>{{ activeDetails.transactions }}</dd>
          </div>
        </dl>

        <div v-if="activeDetails.comparison" class="daily-net-chart__details-comparison">
          <p>
            {{ activeDetails.comparison.label }}:
            {{ formatAmount(activeDetails.comparison.value) }}
          </p>
          <p>
            vs prior:
            {{ activeDetails.comparison.deltaPrefix
            }}{{ formatAmount(activeDetails.comparison.delta)
            }}{{ activeDetails.comparison.percentage }}
          </p>
        </div>
        <button
          v-if="activeDetails.canDrill"
          class="daily-net-chart__drill-btn"
          type="button"
          @click="activateBucket(activeBucket)"
        >
          View daily breakdown
        </button>
      </section>

      <nav v-if="isDrilled" class="daily-net-chart__breadcrumb" aria-label="Chart drilldown">
        <button type="button" class="daily-net-chart__back" @click="exitDrill">
          ← Back to {{ baseGranularityTitle }}
        </button>
        <span class="daily-net-chart__crumb">
          {{ baseGranularityTitle }} › {{ drillLabel }} (Daily)
        </span>
      </nav>

      <div
        class="daily-net-chart__canvas-wrap"
        tabindex="0"
        role="group"
        :aria-label="canvasLabel"
        @keydown="onKeydown"
      >
        <canvas ref="chartCanvas" style="width: 100%; height: 100%" aria-hidden="true"></canvas>
      </div>

      <details class="daily-net-chart__table-disclosure">
        <summary>{{ granularityTitle }} economic net table</summary>
        <div class="daily-net-chart__table-scroll">
          <table class="daily-net-chart__table">
            <caption class="sr-only">
              Economic net by {{ granularityTitle.toLowerCase() }} period
            </caption>
            <thead>
              <tr>
                <th scope="col">Period</th>
                <th scope="col">Income</th>
                <th scope="col">Expenses</th>
                <th scope="col">Refunds</th>
                <th scope="col">Net</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="bucket in buckets"
                :key="bucket.key"
                :class="{ 'is-active': bucket.key === activeBucket?.key }"
              >
                <th scope="row">
                  <button type="button" class="daily-net-chart__row-btn" @click="activateBucket(bucket)">
                    {{ bucketLabel(bucket, 'long') }}
                  </button>
                </th>
                <td>{{ formatAmount(bucket.income) }}</td>
                <td>{{ formatAmount(bucket.expenses) }}</td>
                <td>{{ formatAmount(bucket.refunds) }}</td>
                <td>{{ formatAmount(bucket.net) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
    </template>
  </div>
</template>

<script setup>
/**
 * DailyNetChart.vue
 *
 * Economic net chart. The selected date range is always the global dashboard period;
 * only the bar granularity changes (daily, Monday weeks, months, quarters). The
 * backend `daily_net` rows are the source of truth and are rolled up client-side by
 * `@/utils/dailyNetBuckets`. Clicking a coarse bucket drills into its days inside the
 * chart; clicking a day emits `bar-click` with the ISO date for the owner-scoped modal.
 */
import { fetchDailyNet } from '@/api/charts'
import { ref, computed, onMounted, onUnmounted, nextTick, watch, toRefs } from 'vue'
import { Chart } from 'chart.js'
import { formatAmount } from '@/utils/format'
import { CHART_RANGE_PRESETS } from '@/composables/useDateRange'
import {
  resolveNetGranularity,
  buildNetBuckets,
  formatNetBucketLabel,
  netGranularityTitle,
  formatCompactCurrency,
  resolveComparisonInterval,
  buildComparisonNets,
  sumNetBuckets,
  isoToDay,
  dayToIso,
} from '@/utils/dailyNetBuckets'

import { Legend, LineElement, BarElement, CategoryScale, LinearScale, PointElement } from 'chart.js'

Chart.register(Legend, LineElement, BarElement, CategoryScale, LinearScale, PointElement)

const GRANULARITY_ORDER = ['daily', 'weekly', 'monthly', 'quarterly']
const WARMUP_DAYS = 30

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  zoomedOut: { type: Boolean, default: false },
  show7Day: { type: Boolean, default: false },
  show30Day: { type: Boolean, default: false },
  showAvgIncome: { type: Boolean, default: false },
  showAvgExpenses: { type: Boolean, default: false },
  showComparisonOverlay: { type: Boolean, default: false },
  timeframe: {
    type: String,
    default: 'mtd',
    validator: (value) =>
      value === 'custom' || CHART_RANGE_PRESETS.some((preset) => preset.value === value),
  },
})

const { show7Day, show30Day, showAvgIncome, showAvgExpenses, showComparisonOverlay, timeframe } =
  toRefs(props)

const emit = defineEmits(['bar-click', 'summary-change', 'data-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const comparisonData = ref([])
const comparisonReady = ref(false)
const comparisonError = ref(false)
const isLoading = ref(false)
const hasError = ref(false)
const isEmpty = ref(false)
const legendItems = ref([])
const activeKey = ref(null)
const drill = ref(null)

const getStyle = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

function toParsedValue(value) {
  if (value && typeof value === 'object' && typeof value.parsedValue === 'number')
    return value.parsedValue
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function normalizeZero(value) {
  return Object.is(value, -0) ? 0 : value
}

/** Step the base granularity coarser by one level when the range selector is zoomed out. */
function coarsen(granularity) {
  const next = GRANULARITY_ORDER.indexOf(granularity) + 1
  return GRANULARITY_ORDER[Math.min(next, GRANULARITY_ORDER.length - 1)]
}

const baseGranularity = computed(() => {
  const base = resolveNetGranularity(timeframe.value, props.startDate, props.endDate)
  return props.zoomedOut ? coarsen(base) : base
})
const isDrilled = computed(() => drill.value != null)
const granularity = computed(() => (isDrilled.value ? 'daily' : baseGranularity.value))
const granularityTitle = computed(() => netGranularityTitle(granularity.value))
const baseGranularityTitle = computed(() => netGranularityTitle(baseGranularity.value))

const displayRange = computed(() =>
  isDrilled.value
    ? { start: drill.value.startDate, end: drill.value.endDate }
    : { start: props.startDate, end: props.endDate },
)

const needsWarmup = computed(() => show7Day.value || show30Day.value)
const requestRange = computed(() => {
  const start = isoToDay(props.startDate)
  return {
    startDate: needsWarmup.value && start != null ? dayToIso(start - WARMUP_DAYS) : props.startDate,
    endDate: props.endDate,
  }
})

const multiYear = computed(() => displayRange.value.start.slice(0, 4) !== displayRange.value.end.slice(0, 4))

const buckets = computed(() =>
  buildNetBuckets(chartData.value, displayRange.value.start, displayRange.value.end, granularity.value),
)

const comparisonInterval = computed(() =>
  resolveComparisonInterval(timeframe.value, props.startDate, props.endDate),
)
const comparisonLabel = computed(() => {
  if (timeframe.value === 'mtd') return 'This Day Last Month'
  if (timeframe.value === 'ytd') return 'Same period last year'
  return 'Previous period'
})
const comparisonNets = computed(() => {
  if (!showComparisonOverlay.value || !comparisonReady.value || !comparisonInterval.value) return null
  return buildComparisonNets(
    comparisonData.value,
    buckets.value,
    props.startDate,
    comparisonInterval.value,
  )
})

const hasRefunds = computed(() => buckets.value.some((bucket) => bucket.refunds !== 0))
const baseLegend = computed(() => [
  { label: 'Income', kind: 'bar', color: 'var(--color-accent-green)' },
  { label: 'Expenses', kind: 'bar', color: 'var(--color-accent-red)' },
  ...(hasRefunds.value
    ? [{ label: 'Refunds', kind: 'bar', color: 'var(--color-accent-cyan)' }]
    : []),
  { label: 'Economic net', kind: 'dash', color: 'var(--color-accent-yellow)' },
])

function bucketLabel(bucket, style = 'tick') {
  return formatNetBucketLabel(bucket, { style, multiYear: multiYear.value })
}

function isActiveBucket(bucket) {
  return (
    bucket.income !== 0 ||
    bucket.expenses !== 0 ||
    bucket.refunds !== 0 ||
    bucket.net !== 0 ||
    bucket.transaction_count > 0
  )
}

const activeBucket = computed(() => {
  const list = buckets.value
  if (!list.length) return null
  const keyed = list.find((bucket) => bucket.key === activeKey.value)
  if (keyed) return keyed
  const latest = list[list.length - 1]
  if (isActiveBucket(latest)) return latest
  return list.find(isActiveBucket) ?? latest
})

const drillLabel = computed(() => (drill.value ? bucketLabel(drill.value, 'long') : ''))

/**
 * Create comparison details for the active bucket.
 *
 * @param {number} netValue - Current bucket economic net.
 * @param {string} label - Basis label for the comparison series.
 * @param {number|null} comparisonValue - Net of the matching prior span, or null if unavailable.
 */
function buildComparisonDetails(netValue, label, comparisonValue) {
  if (!label || comparisonValue == null) return null
  const delta = netValue - comparisonValue
  const deltaPrefix = delta >= 0 ? '+' : ''
  const percentage =
    comparisonValue === 0
      ? ''
      : ` (${deltaPrefix}${((delta / Math.abs(comparisonValue)) * 100).toFixed(1)}%)`
  return { label, value: comparisonValue, delta, deltaPrefix, percentage }
}

const activeDetails = computed(() => {
  const bucket = activeBucket.value
  if (!bucket) return null
  const index = buckets.value.indexOf(bucket)
  return {
    key: bucket.key,
    date: bucketLabel(bucket, 'long'),
    isPartial: bucket.isPartial && bucket.granularity !== 'daily',
    net: bucket.net,
    income: bucket.income,
    expenses: bucket.expenses,
    refunds: bucket.refunds,
    transactions: bucket.transaction_count,
    canDrill: bucket.granularity !== 'daily',
    comparison: buildComparisonDetails(
      bucket.net,
      comparisonLabel.value,
      comparisonNets.value?.[index] ?? null,
    ),
  }
})

const canvasLabel = computed(
  () =>
    `Economic net bar chart, ${granularityTitle.value.toLowerCase()}, ${buckets.value.length} periods. ` +
    'Use left and right arrow keys to move between periods and Enter to open one.',
)

function setActiveIndex(index) {
  const bucket = buckets.value[Math.min(Math.max(Math.trunc(index), 0), buckets.value.length - 1)]
  if (bucket) activeKey.value = bucket.key
}

/** Daily bars open the day modal through the parent; coarser bars drill into their days. */
function activateBucket(bucket) {
  if (!bucket) return
  activeKey.value = bucket.key
  if (bucket.granularity === 'daily') {
    emit('bar-click', bucket.startDate)
    return
  }
  drill.value = bucket
  activeKey.value = null
}

function exitDrill() {
  if (!drill.value) return
  activeKey.value = drill.value.key
  drill.value = null
}

function onKeydown(event) {
  const list = buckets.value
  if (!list.length) return
  const current = Math.max(list.indexOf(activeBucket.value), 0)
  const moves = {
    ArrowLeft: current - 1,
    ArrowRight: current + 1,
    Home: 0,
    End: list.length - 1,
  }
  if (event.key in moves) {
    event.preventDefault()
    setActiveIndex(moves[event.key])
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    activateBucket(activeBucket.value)
  } else if (event.key === 'Escape' && isDrilled.value) {
    event.preventDefault()
    exitDrill()
  }
}

/**
 * Daily rows for an inclusive range in the API's `{parsedValue}` shape, zero-filled.
 */
function padDailyRows(rows, startDate, endDate) {
  const first = isoToDay(startDate)
  const last = isoToDay(endDate)
  if (first == null || last == null || last < first) return []
  const byDate = new Map((rows || []).map((row) => [String(row.date).slice(0, 10), row]))
  const padded = []
  for (let day = first; day <= last; day += 1) {
    const iso = dayToIso(day)
    padded.push(
      byDate.get(iso) ?? {
        date: iso,
        income: { parsedValue: 0 },
        expenses: { parsedValue: 0 },
        net: { parsedValue: 0 },
        refunds: 0,
        transaction_count: 0,
      },
    )
  }
  return padded
}

function movingAverage(values, window) {
  return values.map((_, i) =>
    i < window - 1 ? null : values.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0) / window,
  )
}

function mean(values) {
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0
}

function buildLineDataset(label, data, color, overrides = {}) {
  return {
    type: 'line',
    label,
    data,
    borderColor: color,
    backgroundColor: 'transparent',
    borderWidth: 2,
    tension: 0.25,
    pointRadius: 0,
    spanGaps: true,
    fill: false,
    ...overrides,
  }
}

function getBarSizing(count) {
  if (count <= 8) return { maxBarThickness: 64, categoryPercentage: 0.8, barPercentage: 0.8 }
  if (count <= 16) return { maxBarThickness: 40, categoryPercentage: 0.85, barPercentage: 0.85 }
  if (count <= 31) return { maxBarThickness: 26, categoryPercentage: 0.88, barPercentage: 0.85 }
  return { maxBarThickness: 16, categoryPercentage: 0.9, barPercentage: 0.85 }
}

function getTickLimit(count) {
  const compact = typeof window !== 'undefined' && window.innerWidth < 640
  if (count <= (compact ? 7 : 14)) return count
  return compact ? 6 : 10
}

/** Pixel position of the net marker for a bar, centred on the bar and as wide as it. */
function getNetDashPosition(chart, dataIndex) {
  if (!chart?.getDatasetMeta) return null
  const bar = chart.getDatasetMeta(0)?.data?.[dataIndex]
  const yScale = chart.scales?.y
  const netValue = toParsedValue(chart?.$netValues?.[dataIndex])
  if (!bar || !yScale) return null
  return {
    x: bar.x,
    y: yScale.getPixelForValue(netValue),
    width: Math.max(bar.width ?? 20, 12),
  }
}

const netDashPlugin = {
  id: 'netDashPlugin',
  beforeDatasetsDraw(chart) {
    const index = chart.$activeIndex
    const bar = chart?.getDatasetMeta?.(0)?.data?.[index]
    const area = chart?.chartArea
    if (!bar || !area || !chart.ctx?.save) return
    const { ctx } = chart
    const width = Math.max((bar.width ?? 20) + 10, 18)
    ctx.save()
    ctx.fillStyle = 'rgba(128, 128, 128, 0.16)'
    ctx.fillRect(bar.x - width / 2, area.top, width, area.bottom - area.top)
    ctx.restore()
  },
  afterDatasetsDraw(chart) {
    if (!chart?.ctx || !chart?.getDatasetMeta) return
    const firstMeta = chart.getDatasetMeta(0)
    if (!firstMeta?.data?.length) return
    firstMeta.data.forEach((_, index) => {
      const position = getNetDashPosition(chart, index)
      if (!position) return
      const { ctx } = chart
      if (!ctx?.save) return
      const half = position.width / 2 + 3
      ctx.save()
      ctx.lineCap = 'round'
      ctx.strokeStyle = getStyle('--theme-bg-surface') || 'rgba(0,0,0,0.6)'
      ctx.lineWidth = 5
      ctx.beginPath()
      ctx.moveTo(position.x - half, position.y)
      ctx.lineTo(position.x + half, position.y)
      ctx.stroke()
      ctx.strokeStyle = getStyle('--color-accent-yellow')
      ctx.lineWidth = 3
      ctx.stroke()
      ctx.restore()
    })
  },
}

function handleBarClick(evt) {
  if (!chartInstance.value) return
  const points = chartInstance.value.getElementsAtEventForMode(
    evt,
    'nearest',
    { intersect: true },
    false,
  )
  if (points.length) activateBucket(buckets.value[points[0].index])
}

function destroyChart() {
  if (chartInstance.value) {
    chartInstance.value.stop?.()
    chartInstance.value.destroy?.()
    chartInstance.value = null
  }
}

async function renderChart() {
  await nextTick()
  destroyChart()

  if (hasError.value || isLoading.value || isEmpty.value) return

  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  const list = buckets.value
  if (!list.length) return

  const labels = list.map((bucket) => bucket.startDate)
  const tickLabels = list.map((bucket) => bucketLabel(bucket))
  const income = list.map((bucket) => normalizeZero(bucket.income))
  const expenses = list.map((bucket) => normalizeZero(bucket.expenses))
  const refunds = list.map((bucket) => normalizeZero(bucket.refunds))
  const net = list.map((bucket) => bucket.net)
  const sizing = getBarSizing(list.length)

  const incomeColor = getStyle('--color-accent-green') || '#22c55e'
  const expenseColor = getStyle('--color-accent-red') || '#ef4444'
  const refundColor = getStyle('--color-accent-cyan') || '#63cdcf'
  const comparisonColor = getStyle('--color-text-light') || '#f8fafc'
  const sevenDayColor = getStyle('--color-accent-blue') || '#719cd6'
  const thirtyDayColor = getStyle('--color-accent-purple') || '#9d79d6'
  const fontFamily = getStyle('--font-chart') || 'ui-sans-serif, system-ui, sans-serif'
  const textColor = getStyle('--color-text-muted')

  const stackId = 'net-stack'
  const bar = (label, data, color, order) => ({
    type: 'bar',
    label,
    data,
    ...sizing,
    backgroundColor: color,
    borderColor: color,
    borderWidth: 1,
    stack: stackId,
    order,
  })
  const datasets = [
    bar('Expenses', expenses, expenseColor, 1),
    bar('Income', income, incomeColor, 2),
    bar('Refunds', refunds, refundColor, 3),
  ]

  const overlayLabels = []
  const isDaily = granularity.value === 'daily'
  const unit = { daily: 'day', weekly: 'week', monthly: 'month', quarterly: 'quarter' }[
    granularity.value
  ]
  const partialNote = list.some((bucket) => bucket.isPartial) && !isDaily ? ' (incl. partial)' : ''
  const avgLabel = (name) => (isDaily ? name : `${name} / ${unit}${partialNote}`)

  if (showAvgIncome.value) {
    const label = avgLabel('Avg Income')
    const value = mean(income)
    datasets.push(
      buildLineDataset(label, labels.map(() => value), incomeColor, { borderDash: [6, 6], order: 4 }),
    )
    overlayLabels.push(label)
  }

  if (showAvgExpenses.value) {
    const label = avgLabel('Avg Expenses')
    const value = mean(expenses)
    datasets.push(
      buildLineDataset(label, labels.map(() => value), expenseColor, {
        borderDash: [4, 8],
        order: 5,
      }),
    )
    overlayLabels.push(label)
  }

  const comparisonSeries = comparisonNets.value
  if (comparisonSeries) {
    datasets.push(
      buildLineDataset(comparisonLabel.value, comparisonSeries, comparisonColor, {
        borderDash: [8, 8],
        order: 6,
      }),
    )
    overlayLabels.push(comparisonLabel.value)
  }

  // 7/30-day moving averages are daily-net windows: only meaningful against daily bars.
  if (isDaily && (show7Day.value || show30Day.value)) {
    const full = padDailyRows(chartData.value, requestRange.value.startDate, requestRange.value.endDate)
    const fullNet = full.map((row) => toParsedValue(row.net))
    const indexByDate = new Map(full.map((row, i) => [row.date, i]))
    const mapToDisplay = (series) =>
      labels.map((label) => {
        const idx = indexByDate.get(label)
        return idx == null ? null : (series[idx] ?? null)
      })
    if (show30Day.value) {
      datasets.push(
        buildLineDataset('30-Day Avg', mapToDisplay(movingAverage(fullNet, 30)), thirtyDayColor, {
          borderDash: [8, 4],
          borderWidth: 3,
          order: 7,
        }),
      )
      overlayLabels.push('30-Day Avg')
    }
    if (show7Day.value) {
      datasets.push(
        buildLineDataset('7-Day Avg', mapToDisplay(movingAverage(fullNet, 7)), sevenDayColor, {
          borderDash: [2, 2],
          borderWidth: 3,
          order: 8,
        }),
      )
      overlayLabels.push('7-Day Avg')
    }
  }

  legendItems.value = datasets
    .filter((dataset) => overlayLabels.includes(dataset.label))
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
    .map((dataset) => ({ label: dataset.label, color: dataset.borderColor || '#fff' }))

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    plugins: [netDashPlugin],
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      onClick: handleBarClick,
      onHover: (_event, elements) => {
        const index = elements?.[0]?.index
        if (index != null) setActiveIndex(index)
      },
      interaction: { mode: 'index', axis: 'x', intersect: false },
      scales: {
        x: {
          grid: { display: false },
          border: { color: getStyle('--divider') || 'rgba(255,255,255,0.2)' },
          ticks: {
            autoSkip: true,
            maxTicksLimit: getTickLimit(list.length),
            maxRotation: 0,
            color: textColor,
            font: { family: fontFamily, size: 12 },
            callback: (_, index) => tickLabels[index],
          },
        },
        y: {
          stacked: true,
          grid: {
            color: (context) =>
              context.tick?.value === 0
                ? getStyle('--color-text-muted') || 'rgba(255,255,255,0.5)'
                : getStyle('--divider') || 'rgba(255,255,255,0.08)',
            lineWidth: (context) => (context.tick?.value === 0 ? 2 : 1),
          },
          ticks: {
            color: textColor,
            font: { family: fontFamily, size: 12 },
            callback: (value) => formatCompactCurrency(value),
          },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false },
      },
    },
  })

  chartInstance.value.$dailyNetRows = list
  chartInstance.value.$buckets = list
  chartInstance.value.$comparisonSeries = comparisonSeries
  chartInstance.value.$comparisonLabel = comparisonSeries ? comparisonLabel.value : ''
  chartInstance.value.$netValues = net
  chartInstance.value.$activeIndex = list.indexOf(activeBucket.value)
}

watch(activeBucket, (bucket) => {
  const chart = chartInstance.value
  if (!chart) return
  chart.$activeIndex = buckets.value.indexOf(bucket)
  chart.draw?.()
})

let primarySeq = 0
let comparisonSeq = 0

/** Emit the daily rows and totals for the selected (global) period, never the drilled one. */
function emitPeriod() {
  if (isEmpty.value) {
    emit('summary-change', { totalIncome: 0, totalExpenses: 0, totalRefunds: 0, totalNet: 0 })
    emit('data-change', [])
    return
  }
  const daily = padDailyRows(chartData.value, props.startDate, props.endDate)
  emit('summary-change', sumNetBuckets(daily))
  emit('data-change', daily)
}

async function fetchData() {
  const seq = ++primarySeq
  isLoading.value = true
  hasError.value = false
  const { startDate, endDate } = requestRange.value

  try {
    const res = await fetchDailyNet({ start_date: startDate, end_date: endDate })
    if (seq !== primarySeq) return

    if (res.status === 'success') {
      const rows = Array.isArray(res.data) ? res.data : []
      chartData.value = rows
      isEmpty.value = !rows.some((row) => {
        const date = String(row?.date).slice(0, 10)
        return date >= props.startDate && date <= props.endDate
      })
      emitPeriod()
      return
    }

    hasError.value = true
    chartData.value = []
  } catch (_error) {
    if (seq !== primarySeq) return
    hasError.value = true
    chartData.value = []
  } finally {
    if (seq === primarySeq) isLoading.value = false
  }
}

async function fetchComparisonData() {
  const seq = ++comparisonSeq
  comparisonReady.value = false
  comparisonError.value = false

  const interval = comparisonInterval.value
  if (!showComparisonOverlay.value || !interval) {
    comparisonData.value = []
    return
  }

  try {
    const res = await fetchDailyNet({ start_date: interval.start, end_date: interval.end })
    if (seq !== comparisonSeq) return

    if (res.status === 'success') {
      comparisonData.value = Array.isArray(res.data) ? res.data : []
      comparisonReady.value = true
      return
    }
    comparisonError.value = true
    comparisonData.value = []
  } catch (_error) {
    if (seq !== comparisonSeq) return
    comparisonError.value = true
    comparisonData.value = []
  }
}

async function retryFetch() {
  await fetchData()
  await fetchComparisonData()
}

watch(
  [
    buckets,
    comparisonNets,
    isLoading,
    hasError,
    isEmpty,
    show7Day,
    show30Day,
    showAvgIncome,
    showAvgExpenses,
    showComparisonOverlay,
  ],
  renderChart,
)
watch(
  () => [props.startDate, props.endDate, props.zoomedOut, timeframe.value],
  () => {
    drill.value = null
    activeKey.value = null
  },
)
watch(() => [props.startDate, props.endDate, needsWarmup.value], fetchData)
watch(
  () => [timeframe.value, showComparisonOverlay.value, props.startDate, props.endDate],
  fetchComparisonData,
)

onMounted(() => {
  fetchData()
  fetchComparisonData()
})
onUnmounted(() => {
  primarySeq += 1
  comparisonSeq += 1
  destroyChart()
})
</script>

<style scoped>
.daily-net-chart__header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem 1rem;
  margin-bottom: 0.75rem;
}

.daily-net-chart__title-shell {
  flex: 1 1 16rem;
  min-width: 0;
}

.daily-net-chart__controls-shell {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 100%;
  display: flex;
  justify-content: flex-end;
}

.daily-net-chart__state {
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--color-text-muted);
}

.daily-net-chart__state--error {
  color: var(--color-accent-red);
}

.daily-net-chart__retry {
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 0.375rem 0.75rem;
  background: var(--theme-bg-surface, transparent);
  color: inherit;
  cursor: pointer;
}

.daily-net-chart__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.9rem;
  align-items: center;
  margin: 0 0 0.5rem;
  padding: 0;
  list-style: none;
}

.daily-net-chart__legend--overlays {
  gap: 0.35rem 0.5rem;
}

.daily-net-chart__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.daily-net-chart__legend-item.angular-chart-chip {
  padding: 0.22rem 0.5rem;
  border-radius: var(--chart-shell-radius-tight);
}

.daily-net-chart__swatch {
  display: inline-block;
  flex: none;
}

.daily-net-chart__swatch--bar {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 2px;
  background: var(--legend-color);
}

.daily-net-chart__swatch--dash {
  width: 1.1rem;
  border-top: 3px solid var(--legend-color);
}

.daily-net-chart__swatch--dashed {
  width: 1rem;
  border-top: 2px dashed var(--legend-color);
}

.daily-net-chart__legend-label {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-chart__notice {
  margin: 0 0 0.5rem;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-chart__details {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 2fr);
  gap: 0.5rem 1.25rem;
  align-items: center;
  margin-bottom: 0.75rem;
  padding: 0.75rem 1rem;
  border-color: var(--chart-shell-border);
  border-radius: var(--chart-shell-radius-tight);
  background: color-mix(in srgb, var(--theme-bg-surface, var(--theme-bg)) 90%, transparent);
}

.daily-net-chart__details-header {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.daily-net-chart__details-date {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-chart__details-partial {
  margin-left: 0.35rem;
  padding: 0 0.35rem;
  border: 1px solid var(--divider);
  border-radius: 999px;
  font-size: 0.75rem;
}

.daily-net-chart__details-net {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-light);
}

.daily-net-chart__details-net.is-positive {
  color: var(--color-accent-green);
}

.daily-net-chart__details-net.is-negative {
  color: var(--color-accent-red);
}

.daily-net-chart__details-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.4rem;
  margin: 0;
}

.daily-net-chart__details-metrics div {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.daily-net-chart__details-metrics dt {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-chart__details-metrics dd {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-light);
}

.daily-net-chart__details-comparison {
  grid-column: 1 / -1;
  padding-top: 0.4rem;
  border-top: 1px solid var(--divider);
  font-size: 0.8125rem;
  color: var(--color-text-light);
}

.daily-net-chart__details-comparison p {
  margin: 0;
}

.daily-net-chart__details-comparison p + p {
  margin-top: 0.125rem;
  color: var(--color-accent-yellow);
}

.daily-net-chart__drill-btn,
.daily-net-chart__back {
  justify-self: start;
  padding: 0.25rem 0.6rem;
  border: 1px solid var(--divider);
  border-radius: var(--chart-shell-radius-tight);
  background: transparent;
  color: var(--color-text-light);
  font-size: 0.8125rem;
  cursor: pointer;
}

.daily-net-chart__drill-btn:focus-visible,
.daily-net-chart__back:focus-visible,
.daily-net-chart__row-btn:focus-visible,
.daily-net-chart__canvas-wrap:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.daily-net-chart__breadcrumb {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
  margin-bottom: 0.5rem;
}

.daily-net-chart__crumb {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-chart__canvas-wrap {
  position: relative;
  height: clamp(260px, 45vh, 400px);
}

.daily-net-chart__table-disclosure {
  margin-top: 0.75rem;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
}

.daily-net-chart__table-disclosure summary {
  cursor: pointer;
  width: fit-content;
}

.daily-net-chart__table-scroll {
  max-width: 100%;
  max-height: 18rem;
  overflow: auto;
  margin-top: 0.5rem;
}

.daily-net-chart__table {
  width: 100%;
  border-collapse: collapse;
  color: var(--color-text-light);
}

.daily-net-chart__table th,
.daily-net-chart__table td {
  padding: 0.25rem 0.5rem;
  border-bottom: 1px solid var(--divider);
  text-align: right;
  white-space: nowrap;
  font-weight: 400;
}

.daily-net-chart__table th:first-child {
  text-align: left;
}

.daily-net-chart__table tr.is-active {
  background: color-mix(in srgb, var(--color-accent-yellow) 12%, transparent);
}

.daily-net-chart__row-btn {
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  text-decoration: underline;
  cursor: pointer;
}

@media (max-width: 900px) {
  .daily-net-chart__controls-shell {
    flex-basis: 100%;
    justify-content: flex-start;
  }

  .daily-net-chart__details {
    grid-template-columns: minmax(0, 1fr);
  }

  .daily-net-chart__details-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
