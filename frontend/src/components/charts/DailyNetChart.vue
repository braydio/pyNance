<template>
  <div class="daily-net-chart">
    <div v-if="hasError" class="daily-net-chart__state daily-net-chart__state--error">
      <p>Unable to load daily net data right now. Please try again.</p>
      <button class="daily-net-chart__retry" type="button" @click="retryFetch">Retry</button>
    </div>

    <div v-else-if="isLoading" class="daily-net-chart__state">Loading daily net chart…</div>

    <div v-else-if="isEmpty" class="daily-net-chart__state">
      No transactions found for the selected date range.
    </div>

    <template v-else>
      <div
        v-if="legendItems.length"
        class="daily-net-chart__legend"
        aria-label="Active chart overlays"
      >
        <span
          v-for="item in legendItems"
          :key="item.label"
          class="daily-net-chart__legend-item"
          :style="{ '--legend-color': item.color }"
        >
          <span class="daily-net-chart__legend-swatch" />
          <span class="daily-net-chart__legend-label">{{ item.label }}</span>
        </span>
      </div>

      <div class="daily-net-chart__canvas-wrap">
        <canvas ref="chartCanvas" style="width: 100%; height: 100%"></canvas>
        <section
          v-if="activeDetails"
          class="daily-net-chart__details"
          aria-live="polite"
          aria-label="Active day details"
        >
          <div class="daily-net-chart__details-header">
            <p class="daily-net-chart__details-date">{{ activeDetails.date }}</p>
            <p class="daily-net-chart__details-net">Net: {{ formatAmount(activeDetails.net) }}</p>
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
              <dt>Transactions</dt>
              <dd>{{ activeDetails.transactions }}</dd>
            </div>
          </dl>

          <div v-if="activeDetails.comparison" class="daily-net-chart__details-comparison">
            <p>
              {{ activeDetails.comparison.label }}: {{ formatAmount(activeDetails.comparison.value) }}
            </p>
            <p>
              vs prior:
              {{ activeDetails.comparison.deltaPrefix
              }}{{ formatAmount(activeDetails.comparison.delta)
              }}{{ activeDetails.comparison.percentage }}
            </p>
          </div>
        </section>
        <div
          v-show="hoverIndicator.visible"
          class="daily-net-chart__hover-indicator"
          :style="{ left: `${hoverIndicator.x}px`, top: `${hoverIndicator.y}px` }"
          aria-hidden="true"
        >
          <span class="daily-net-chart__hover-dot" />
          <span class="daily-net-chart__hover-label">{{ hoverIndicator.label }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
/**
 * DailyNetChart.vue
 *
 * Renders the dashboard daily net chart with stacked income/expense bars,
 * a net indicator dash, and a persistent details panel for the active day.
 */
import { fetchDailyNet } from '@/api/charts'
import { ref, onMounted, onUnmounted, nextTick, watch, toRefs } from 'vue'
import { Chart } from 'chart.js'
import { formatAmount } from '@/utils/format'

import { Legend, LineElement, BarElement, CategoryScale, LinearScale, PointElement } from 'chart.js'

Chart.register(Legend, LineElement, BarElement, CategoryScale, LinearScale, PointElement)

function toParsedValue(value) {
  if (value && typeof value === 'object' && typeof value.parsedValue === 'number')
    return value.parsedValue
  return typeof value === 'number' ? value : 0
}

function normalizeZero(value) {
  return Object.is(value, -0) ? 0 : value
}

/**
 * Resolve the pixel position for the net indicator at a given label index.
 *
 * @param {import('chart.js').Chart} chart - The chart instance.
 * @param {number} dataIndex - Active label index.
 * @returns {{x: number, y: number} | null} Pixel coordinates for the net dash.
 */
function getNetDashPosition(chart, dataIndex) {
  if (!chart?.getDatasetMeta) return null
  const firstMeta = chart.getDatasetMeta(0)
  const bar = firstMeta?.data?.[dataIndex]
  const yScale = chart.scales?.y
  const netValue = toParsedValue(
    chart?.$netValues?.[dataIndex] ?? chart?.$dailyNetRows?.[dataIndex]?.net,
  )
  if (!bar || !yScale) return null
  return { x: bar.x, y: yScale.getPixelForValue(netValue) }
}

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
    validator: (value) => ['mtd', 'rolling_30'].includes(value),
  },
})

const { show7Day, show30Day, showAvgIncome, showAvgExpenses, showComparisonOverlay, timeframe } =
  toRefs(props)

const emit = defineEmits(['bar-click', 'summary-change', 'data-change'])

const chartInstance = ref(null)
const chartCanvas = ref(null)
const chartData = ref([])
const comparisonData = ref([])
const requestRange = ref({ startDate: null, endDate: null, displayStart: null, displayEnd: null })
const isLoading = ref(false)
const hasError = ref(false)
const isEmpty = ref(false)
const legendItems = ref([])
const activeIndex = ref(null)
const activeDetails = ref(null)
const hoverIndicator = ref({ x: 0, y: 0, visible: false, label: '' })

const MS_PER_DAY = 86400000
const DEFAULT_ZOOM_MONTHS = 6

const getStyle = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

/**
 * Create comparison details for the active point using the existing tooltip math.
 *
 * @param {number} netValue - Current period net value.
 * @param {string} comparisonLabel - Prior-series label.
 * @param {number|null} comparisonValue - Prior-series value at the same aligned index.
 * @returns {{label: string, value: number, delta: number, deltaPrefix: string, percentage: string}|null}
 * Comparison details used by the persistent details panel.
 */
function buildComparisonDetails(netValue, comparisonLabel, comparisonValue) {
  if (!comparisonLabel || comparisonValue == null) return null

  const delta = netValue - comparisonValue
  const deltaPrefix = delta >= 0 ? '+' : ''
  const percentage =
    comparisonValue === 0
      ? ''
      : ` (${deltaPrefix}${((delta / Math.abs(comparisonValue)) * 100).toFixed(1)}%)`

  return { label: comparisonLabel, value: comparisonValue, delta, deltaPrefix, percentage }
}

function isNonEmptyDailyRow(row) {
  return (
    toParsedValue(row?.income) !== 0 ||
    toParsedValue(row?.expenses) !== 0 ||
    toParsedValue(row?.net) !== 0 ||
    (row?.transaction_count ?? 0) > 0
  )
}

function resolveInitialActiveIndex(displayData) {
  if (!displayData.length) return null
  const latestIndex = displayData.length - 1
  if (isNonEmptyDailyRow(displayData[latestIndex])) return latestIndex
  const firstNonEmptyIndex = displayData.findIndex((row) => isNonEmptyDailyRow(row))
  return firstNonEmptyIndex >= 0 ? firstNonEmptyIndex : latestIndex
}

function resolveDetailsFromIndex(index, labels, displayData, comparisonSeries, comparisonLabel) {
  const row = displayData[index]
  const label = labels[index]
  if (row == null || !label) return null

  const netValue = toParsedValue(row.net)
  const comparisonValue = comparisonSeries?.[index] ?? null
  const comparison = buildComparisonDetails(netValue, comparisonLabel, comparisonValue)

  return {
    date: formatTooltipTitle(label),
    net: netValue,
    income: toParsedValue(row.income),
    expenses: toParsedValue(row.expenses),
    transactions: row?.transaction_count ?? 0,
    comparison,
  }
}

function clampActiveIndex(index, size) {
  if (!Number.isFinite(index) || size <= 0) return null
  return Math.min(Math.max(Math.trunc(index), 0), size - 1)
}

function getChartPayloadAtIndex(index) {
  const chart = chartInstance.value
  const labels = chart?.data?.labels ?? []
  const displayData = chart?.$dailyNetRows ?? []
  const comparisonSeries = chart?.$comparisonSeries
  const comparisonLabel = chart?.$comparisonLabel
  const clampedIndex = clampActiveIndex(index, labels.length)

  if (clampedIndex == null) return null

  const details = resolveDetailsFromIndex(
    clampedIndex,
    labels,
    displayData,
    comparisonSeries,
    comparisonLabel,
  )
  return details ? { index: clampedIndex, details } : null
}

function setActivePoint(index) {
  const payload = getChartPayloadAtIndex(index)
  if (!payload) return false

  activeIndex.value = payload.index
  activeDetails.value = payload.details
  return true
}

function resolveEventPoint(event) {
  const native = event?.native ?? event
  const x = Number.isFinite(native?.offsetX) ? native.offsetX : null
  const y = Number.isFinite(native?.offsetY) ? native.offsetY : null
  return { x, y }
}

function updateHoverIndicator(event, index) {
  const chart = chartInstance.value
  if (!chart) return

  const meta = chart.getDatasetMeta(0)
  const bar = meta?.data?.[index]
  if (!bar) {
    hoverIndicator.value.visible = false
    return
  }

  const labels = chart.data?.labels ?? []
  const label = typeof labels[index] === 'string' ? labels[index] : ''
  const { x: eventX, y: eventY } = resolveEventPoint(event)
  const chartArea = chart.chartArea
  const barTop = Math.min(bar.y, bar.base)
  const offsetY = Number.isFinite(eventY) ? Math.min(eventY, barTop) : barTop
  const rawX = Number.isFinite(eventX) ? eventX : bar.x
  const rawY = offsetY - 12
  const minX = (chartArea?.left ?? 0) + 8
  const maxX = (chartArea?.right ?? rawX) - 8
  const minY = (chartArea?.top ?? 0) + 8
  const clampedX = Math.min(Math.max(rawX, minX), maxX)
  const clampedY = Math.max(rawY, minY)

  hoverIndicator.value = {
    x: clampedX,
    y: clampedY,
    visible: true,
    label: formatTooltipTitle(label),
  }
}

function formatDateKey(date) {
  const d = date instanceof Date && !Number.isNaN(date) ? date : new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}

function parseDateKey(str) {
  if (!str) return null
  const d = new Date(`${str}T00:00:00`)
  return Number.isNaN(d) ? null : d
}

const formatTooltipTitle = (label) => {
  const parsed = parseDateKey(label)
  return parsed
    ? parsed.toLocaleDateString(undefined, { month: 'short', day: '2-digit', year: 'numeric' })
    : label
}

function formatAxisLabel(label) {
  const parsed = parseDateKey(label)
  return parsed ? parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : label
}

function formatAxisMonthLabel(label) {
  const parsed = parseDateKey(label)
  return parsed ? parsed.toLocaleDateString(undefined, { month: 'short' }) : label
}

function getDensityConfig(labelCount) {
  if (labelCount >= 120) {
    return {
      barThickness: 5,
      maxBarThickness: 8,
      categoryPercentage: 0.92,
      barPercentage: 0.8,
      maxTicksLimit: 6,
      axisFormatter: formatAxisMonthLabel,
    }
  }

  if (labelCount >= 45) {
    return {
      barThickness: 10,
      maxBarThickness: 14,
      categoryPercentage: 0.88,
      barPercentage: 0.82,
      maxTicksLimit: 8,
      axisFormatter: formatAxisLabel,
    }
  }

  return {
    barThickness: 18,
    maxBarThickness: 22,
    categoryPercentage: 0.85,
    barPercentage: 0.9,
    maxTicksLimit: 8,
    axisFormatter: formatAxisLabel,
  }
}

function buildDateRangeLabels(startDate, endDate) {
  const start = parseDateKey(startDate)
  const end = parseDateKey(endDate)
  if (!start || !end) return []

  const labels = []
  const cur = new Date(Math.min(start, end))
  const last = new Date(Math.max(start, end))

  while (cur <= last) {
    labels.push(formatDateKey(cur))
    cur.setDate(cur.getDate() + 1)
  }

  return labels
}

function createEmptyDailyNetEntry(date) {
  return {
    date,
    income: { parsedValue: 0 },
    expenses: { parsedValue: 0 },
    net: { parsedValue: 0 },
    transaction_count: 0,
  }
}

function padDailyNetData(data, labels) {
  const map = new Map((data || []).map((d) => [d.date, d]))
  return labels.map((l) => map.get(l) ?? createEmptyDailyNetEntry(l))
}

function movingAverage(values, window) {
  return values.map((_, i) =>
    i < window - 1 ? null : values.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0) / window,
  )
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

function emphasizeColor(hex, channel = 'g') {
  return hex
}

function getZoomedDisplayRange() {
  const end = parseDateKey(props.endDate) ?? new Date()
  const start = parseDateKey(props.startDate) ?? new Date(end)
  if (!props.startDate) start.setMonth(start.getMonth() - DEFAULT_ZOOM_MONTHS)
  return { startDate: formatDateKey(start), endDate: formatDateKey(end) }
}

function getActiveLabelRange() {
  if (!props.zoomedOut) return { startDate: props.startDate, endDate: props.endDate }

  const zoomed = getZoomedDisplayRange()
  return {
    startDate: props.startDate || requestRange.value.displayStart || zoomed.startDate,
    endDate: props.endDate || requestRange.value.displayEnd || zoomed.endDate,
  }
}

function getDisplaySeries() {
  const { startDate, endDate } = getActiveLabelRange()
  const labels = buildDateRangeLabels(startDate, endDate)
  return { labels, displayData: padDailyNetData(chartData.value, labels) }
}

function getExtendedSeries() {
  const displayRange = getActiveLabelRange()
  const startDate = requestRange.value.startDate || displayRange.startDate
  const endDate = requestRange.value.endDate || displayRange.endDate
  const labels = buildDateRangeLabels(startDate, endDate)
  return { labels, fullData: padDailyNetData(chartData.value, labels) }
}

function mapSeriesToDisplay(labels, fullLabels, fullSeries) {
  const labelIndex = new Map(fullLabels.map((label, index) => [label, index]))
  return labels.map((label) => {
    const idx = labelIndex.get(label)
    return idx == null ? null : (fullSeries[idx] ?? null)
  })
}

function buildComparisonContext() {
  const end = parseDateKey(props.endDate)
  const start = parseDateKey(props.startDate)
  if (!end || !start) return null

  if (timeframe.value === 'mtd') {
    const priorMonthStart = new Date(end.getFullYear(), end.getMonth() - 1, 1)
    const last = new Date(end.getFullYear(), end.getMonth(), 0)
    const day = Math.min(end.getDate(), last.getDate())
    return {
      mode: 'prior_month_to_date',
      priorStart: priorMonthStart,
      priorEnd: new Date(priorMonthStart.getFullYear(), priorMonthStart.getMonth(), day),
    }
  }

  const currentStart = start
  const priorEnd = new Date(currentStart)
  priorEnd.setDate(priorEnd.getDate() - 1)
  const priorStart = new Date(priorEnd)
  priorStart.setDate(priorStart.getDate() - 29)

  return { mode: 'rolling_30', priorStart, priorEnd, currentStart }
}

function buildComparisonSeries(labels, data, ctx) {
  if (!ctx) return []
  if (ctx.mode === 'prior_month_to_date') {
    const byDay = new Map()
    data.forEach((d) => {
      const parsed = parseDateKey(d.date)
      if (parsed) byDay.set(parsed.getDate(), toParsedValue(d.net))
    })
    return labels.map((l) => {
      const parsed = parseDateKey(l)
      return parsed ? (byDay.get(parsed.getDate()) ?? null) : null
    })
  }

  const byIndex = new Map()
  data.forEach((d) => {
    const parsed = parseDateKey(d.date)
    if (!parsed) return
    const idx = Math.floor((parsed - ctx.priorStart) / MS_PER_DAY)
    if (idx >= 0 && idx < 30) byIndex.set(idx, toParsedValue(d.net))
  })

  return labels.map((l) => {
    const parsed = parseDateKey(l)
    if (!parsed) return null
    const idx = Math.floor((parsed - ctx.currentStart) / MS_PER_DAY)
    return byIndex.get(idx) ?? null
  })
}

const netDashPlugin = {
  id: 'netDashPlugin',
  afterDatasetsDraw(chart) {
    if (!chart?.ctx || !chart?.getDatasetMeta) return
    const firstMeta = chart.getDatasetMeta(0)
    if (!firstMeta?.data?.length) return

    firstMeta.data.forEach((_, index) => {
      const position = getNetDashPosition(chart, index)
      if (!position) return
      const { x, y } = position
      const { ctx } = chart
      if (!ctx?.save) return
      ctx.save()
      ctx.strokeStyle = getStyle('--color-accent-yellow')
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(x - 10, y)
      ctx.lineTo(x + 10, y)
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
  if (points.length) {
    const index = points[0].index
    emit('bar-click', chartInstance.value.data.labels[index])
    setActivePoint(index)
  }
}

async function renderChart() {
  await nextTick()
  if (chartInstance.value) {
    chartInstance.value.stop()
    chartInstance.value.destroy()
  }

  if (hasError.value || isLoading.value) return

  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  const { labels, displayData } = getDisplaySeries()
  const { labels: fullLabels, fullData } = getExtendedSeries()
  if (!labels.length) return

  const hasTransactions = chartData.value.length > 0
  isEmpty.value = !hasTransactions
  if (isEmpty.value) return

  emit(
    'summary-change',
    displayData.reduce(
      (a, r) => ({
        totalIncome: a.totalIncome + toParsedValue(r.income),
        totalExpenses: a.totalExpenses + toParsedValue(r.expenses),
        totalNet: a.totalNet + toParsedValue(r.net),
      }),
      { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
    ),
  )
  emit('data-change', displayData)

  const income = displayData.map((d) => normalizeZero(toParsedValue(d.income)))
  const expenses = displayData.map((d) => normalizeZero(toParsedValue(d.expenses)))
  const net = displayData.map((d) => toParsedValue(d.net))
  const fullNet = fullData.map((d) => toParsedValue(d.net))
  const fullIncome = fullData.map((d) => toParsedValue(d.income))
  const fullExpenses = fullData.map((d) => toParsedValue(d.expenses))
  const full7Day = movingAverage(fullNet, 7)
  const full30Day = movingAverage(fullNet, 30)
  const display7Day = mapSeriesToDisplay(labels, fullLabels, full7Day)
  const display30Day = mapSeriesToDisplay(labels, fullLabels, full30Day)
  const averageIncome = fullIncome.length
    ? fullIncome.reduce((a, b) => a + b, 0) / fullIncome.length
    : 0
  const averageExpenses = fullExpenses.length
    ? fullExpenses.reduce((a, b) => a + b, 0) / fullExpenses.length
    : 0
  const density = getDensityConfig(labels.length)

  const incomeColor = getStyle('--color-accent-green') || '#22c55e'
  const expenseColor = getStyle('--color-accent-red') || '#ef4444'
  const averageIncomeColor = emphasizeColor(incomeColor, 'g')
  const averageExpensesColor = emphasizeColor(expenseColor, 'r')
  const comparisonColor = getStyle('--color-text-light') || '#f8fafc'
  const sevenDayColor = getStyle('--color-accent-cyan') || '#63cdcf'
  const thirtyDayColor = getStyle('--color-accent-purple') || '#9d79d6'
  const fontFamily = getStyle('--font-chart') || 'ui-sans-serif, system-ui, sans-serif'

  const stackId = 'daily-stack'
  const datasets = [
    {
      type: 'bar',
      label: 'Expenses',
      data: expenses,
      barThickness: density.barThickness,
      maxBarThickness: density.maxBarThickness,
      categoryPercentage: density.categoryPercentage,
      barPercentage: density.barPercentage,
      backgroundColor: expenseColor,
      borderColor: expenseColor,
      borderWidth: 1,
      stack: stackId,
      order: 1,
    },
    {
      type: 'bar',
      label: 'Income',
      data: income,
      barThickness: density.barThickness,
      maxBarThickness: density.maxBarThickness,
      categoryPercentage: density.categoryPercentage,
      barPercentage: density.barPercentage,
      backgroundColor: incomeColor,
      borderColor: incomeColor,
      borderWidth: 1,
      stack: stackId,
      order: 2,
    },
  ]

  if (showAvgIncome.value) {
    datasets.push(
      buildLineDataset(
        'Avg Income',
        labels.map(() => averageIncome),
        averageIncomeColor,
        {
          borderDash: [6, 6],
          order: 4,
        },
      ),
    )
  }

  if (showAvgExpenses.value) {
    datasets.push(
      buildLineDataset(
        'Avg Expenses',
        labels.map(() => averageExpenses),
        averageExpensesColor,
        {
          borderDash: [4, 8],
          order: 5,
        },
      ),
    )
  }

  let comparisonSeries = null
  let comparisonLabel = ''

  if (showComparisonOverlay.value) {
    const ctx = buildComparisonContext()
    comparisonSeries = buildComparisonSeries(labels, comparisonData.value, ctx)
    comparisonLabel = 'This Day Last Month'
    datasets.push(
      buildLineDataset(comparisonLabel, comparisonSeries, comparisonColor, {
        borderDash: [8, 8],
        order: 6,
      }),
    )
  }

  if (show30Day.value) {
    datasets.push(
      buildLineDataset('30-Day Avg', display30Day, thirtyDayColor, {
        borderDash: [8, 4],
        borderWidth: 3,
        order: 7,
      }),
    )
  }

  if (show7Day.value) {
    datasets.push(
      buildLineDataset('7-Day Avg', display7Day, sevenDayColor, {
        borderDash: [2, 2],
        borderWidth: 3,
        order: 8,
      }),
    )
  }

  legendItems.value = datasets
    .filter((dataset) =>
      ['Avg Income', 'Avg Expenses', '30-Day Avg', '7-Day Avg'].includes(dataset.label),
    )
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
      onHover: (event, elements) => {
        const index = elements?.[0]?.index
        if (index == null) {
          hoverIndicator.value.visible = false
          return
        }
        setActivePoint(index)
        updateHoverIndicator(event, index)
      },
      onLeave: () => {
        hoverIndicator.value.visible = false
      },
      interaction: {
        mode: 'index',
        axis: 'x',
        intersect: false,
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            autoSkip: true,
            maxTicksLimit: density.maxTicksLimit,
            color: getStyle('--color-text-muted'),
            font: { family: fontFamily, size: 12 },
            callback: (_, index) => density.axisFormatter(labels[index]),
          },
        },
        y: {
          stacked: true,
          grid: { color: getStyle('--divider') || 'rgba(255,255,255,0.08)' },
          ticks: {
            color: getStyle('--color-text-muted'),
            font: { family: fontFamily, size: 12 },
            callback: (value) => formatAmount(value),
          },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: false,
        },
      },
    },
  })

  chartInstance.value.$dailyNetRows = displayData
  chartInstance.value.$comparisonSeries = comparisonSeries
  chartInstance.value.$comparisonLabel = comparisonLabel
  chartInstance.value.$netValues = net

  const nextActiveIndex =
    activeIndex.value == null
      ? resolveInitialActiveIndex(displayData)
      : clampActiveIndex(activeIndex.value, labels.length)

  if (nextActiveIndex != null) {
    setActivePoint(nextActiveIndex)
  }
}

async function fetchData() {
  isLoading.value = true
  hasError.value = false

  const display = props.zoomedOut ? getZoomedDisplayRange() : props
  const start = parseDateKey(display.startDate) ?? new Date()
  start.setDate(start.getDate() - 30)

  requestRange.value = {
    startDate: formatDateKey(start),
    endDate: display.endDate,
    displayStart: display.startDate,
    displayEnd: display.endDate,
  }

  try {
    const res = await fetchDailyNet({
      start_date: requestRange.value.startDate,
      end_date: requestRange.value.endDate,
    })

    if (res.status === 'success') {
      chartData.value = res.data
      return
    }

    hasError.value = true
    chartData.value = []
  } catch (_error) {
    hasError.value = true
    chartData.value = []
  } finally {
    isLoading.value = false
  }
}

async function fetchComparisonData() {
  if (!showComparisonOverlay.value) {
    comparisonData.value = []
    return
  }

  const ctx = buildComparisonContext()
  if (!ctx) {
    comparisonData.value = []
    return
  }

  try {
    const res = await fetchDailyNet({
      start_date: formatDateKey(ctx.priorStart),
      end_date: formatDateKey(ctx.priorEnd),
    })

    if (res.status === 'success') {
      comparisonData.value = res.data
      return
    }

    hasError.value = true
    comparisonData.value = []
  } catch (_error) {
    hasError.value = true
    comparisonData.value = []
  }
}

async function retryFetch() {
  await fetchData()
  await fetchComparisonData()
}

watch(
  [
    chartData,
    comparisonData,
    show7Day,
    show30Day,
    showAvgIncome,
    showAvgExpenses,
    showComparisonOverlay,
    timeframe,
  ],
  renderChart,
)
watch(() => [props.startDate, props.endDate, props.zoomedOut], fetchData)
watch(
  () => [timeframe.value, showComparisonOverlay.value, props.startDate, props.endDate],
  fetchComparisonData,
)

onMounted(() => {
  fetchData()
  fetchComparisonData()
})
onUnmounted(() => chartInstance.value?.destroy())
</script>

<style scoped>
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
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.daily-net-chart__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.daily-net-chart__legend-swatch {
  width: 1rem;
  border-top: 2px dashed var(--legend-color);
}

.daily-net-chart__legend-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.daily-net-chart__details {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  z-index: 2;
  max-width: min(280px, 70%);
  padding: 0.5rem 0.65rem;
  border: 1px solid var(--divider);
  border-radius: 10px;
  background: color-mix(in srgb, var(--theme-bg-surface, var(--theme-bg)) 88%, transparent);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(6px);
}

.daily-net-chart__details-header {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.daily-net-chart__details-date {
  margin: 0;
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.daily-net-chart__details-net {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-accent-yellow);
}

.daily-net-chart__details-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.4rem;
  margin: 0.4rem 0 0;
}

.daily-net-chart__details-metrics div {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.daily-net-chart__details-metrics dt {
  margin: 0;
  font-size: 0.65rem;
  color: var(--color-text-muted);
}

.daily-net-chart__details-metrics dd {
  margin: 0;
  font-size: 0.75rem;
  color: var(--color-text-light);
}

.daily-net-chart__details-comparison {
  margin-top: 0.4rem;
  padding-top: 0.4rem;
  border-top: 1px solid var(--divider);
  font-size: 0.7rem;
  color: var(--color-text-light);
}

.daily-net-chart__details-comparison p {
  margin: 0;
}

.daily-net-chart__details-comparison p + p {
  margin-top: 0.125rem;
  color: var(--color-accent-yellow);
}

.daily-net-chart__canvas-wrap {
  position: relative;
  height: 400px;
}

.daily-net-chart__hover-indicator {
  position: absolute;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.4rem;
  border-radius: 999px;
  border: 1px solid var(--divider);
  background: color-mix(in srgb, var(--theme-bg-surface, var(--theme-bg)) 92%, transparent);
  color: var(--color-text-light);
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  transform: translate(-50%, -100%);
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.2);
}

.daily-net-chart__hover-dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 999px;
  background: var(--color-accent-cyan);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-accent-cyan) 25%, transparent);
}

.daily-net-chart__hover-label {
  color: var(--color-text-light);
}
</style>
