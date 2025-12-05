<template>
  <div
    class="relative w-full max-w-full bg-[var(--theme-bg)] rounded-xl overflow-hidden border border-[var(--divider)]"
    :style="{ height: chartHeight }"
  >
    <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
    <div
      v-if="showEmptyState"
      class="absolute inset-0 flex items-center justify-center text-center px-6 text-[var(--color-text-muted)]"
    >
      Select at least one category to see spending.
    </div>
  </div>
</template>

<script setup>
// CategoryBreakdownChart.vue
// Displays a thin horizontal bar chart of spending by selected category or merchant.
// Defaults to grouping smaller parent categories into an "Other" bucket unless
// `groupOthers` is set to `false`.
import { ref, watch, nextTick, onMounted, onUnmounted, toRefs, computed } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree, fetchMerchantBreakdown } from '@/api/charts'
import { formatAmount } from '@/utils/format'
import { getAccentColor } from '@/utils/colors'

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  selectedCategoryIds: { type: Array, default: () => [] },
  groupOthers: { type: Boolean, default: true },
  breakdownType: {
    type: String,
    default: 'category',
    validator: (value) => ['category', 'merchant'].includes(value),
  },
})

const { startDate, endDate, selectedCategoryIds, groupOthers, breakdownType } = toRefs(props)

const emit = defineEmits(['bar-click', 'summary-change', 'categories-change'])

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryTree = ref([])
const barRows = ref([])
const showEmptyState = computed(() => (selectedCategoryIds.value?.length || 0) === 0)
const chartHeight = computed(() => {
  const rows = barRows.value.length || 0
  const base = 220
  const perRow = 36
  return `${Math.max(base, rows * perRow)}px`
})

// Cycle through theme accent colors for each dataset segment
function getGroupColor(idx) {
  return getAccentColor(idx)
}

function destroyPreviousChart(canvasEl) {
  if (!canvasEl) return
  const prev = Chart.getChart(canvasEl)
  if (prev) prev.destroy()
  chartInstance.value = null
}

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function mapMerchantBreakdownToTree(raw = []) {
  return (raw || []).map((merchant) => ({
    id: merchant.label,
    label: merchant.label,
    amount: merchant.amount,
    children: [
      {
        id: merchant.label,
        label: merchant.label,
        amount: merchant.amount,
      },
    ],
  }))
}

function extractHorizontalBarData(tree, selectedIds = []) {
  const sel = new Set((selectedIds || []).map((x) => String(x)))
  const rows =
    tree?.flatMap((parent) =>
      (parent.children || [])
        .filter((child) => sel.has(String(child.id)))
        .map((child) => ({
          id: String(child.id),
          label: child.label || parent.label || 'Category',
          parentLabel: parent.label || '',
          amount: child.amount || 0,
        })),
    ) || []

  return rows.sort((a, b) => (b.amount || 0) - (a.amount || 0))
}

async function renderChart() {
  await nextTick()
  const canvasEl = chartCanvas.value
  if (!canvasEl) return
  destroyPreviousChart(canvasEl)
  const ctx = canvasEl.getContext('2d')
  if (!ctx) return

  // If nothing is selected, do not render a chart; show the empty-state overlay instead
  if (showEmptyState.value) {
    barRows.value = []
    return
  }

  const rows = extractHorizontalBarData(categoryTree.value, selectedCategoryIds.value)
  barRows.value = rows

  // If there are no rows to show (e.g., selected IDs do not match current data),
  // avoid rendering an empty chart.
  if (!rows.length) {
    return
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: rows.map((row) => row.label),
      datasets: [
        {
          label: 'Spend',
          data: rows.map((row) => row.amount),
          backgroundColor: rows.map((_, idx) => getGroupColor(idx)),
          borderRadius: 10,
          borderSkipped: false,
          barThickness: 14,
          maxBarThickness: 18,
          minBarLength: 6,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 12, bottom: 12, left: 12, right: 18 } },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          mode: 'nearest',
          intersect: true,
          displayColors: true,
          callbacks: {
            title: (items) => {
              const row = barRows.value[items[0]?.dataIndex ?? 0]
              if (!row) return ''
              return row.parentLabel ? `${row.label} • ${row.parentLabel}` : row.label
            },
            label: (context) => `Spend: ${formatAmount(context.raw || 0)}`,
          },
          backgroundColor: getStyle('--theme-bg'),
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
        },
      },
      onClick(evt) {
        if (!chartInstance.value) return
        const points = chartInstance.value.getElementsAtEventForMode(
          evt,
          'nearest',
          { intersect: true },
          false,
        )
        if (points.length) {
          const index = points[0].index
          const row = barRows.value[index]
          if (!row) return
          emit('bar-click', { label: row.label, ids: [row.id] })
        }
      },
      scales: {
        y: {
          display: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
        },
        x: {
          display: true,
          beginAtZero: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            callback: (value) => formatAmount(value),
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 13 },
          },
        },
      },
    },
  })
}

async function fetchData() {
  try {
    const params = {
      start_date: startDate.value,
      end_date: endDate.value,
      top_n: 50,
    }

    const response =
      breakdownType.value === 'merchant'
        ? await fetchMerchantBreakdown(params)
        : await fetchCategoryBreakdownTree(params)
    if (response.status === 'success') {
      const raw = response.data || []
      const normalizedTree =
        breakdownType.value === 'merchant' ? mapMerchantBreakdownToTree(raw) : raw
      let processed = normalizedTree
      if (groupOthers.value && normalizedTree.length > 4) {
        const topFour = normalizedTree.slice(0, 4)
        const others = normalizedTree.slice(4)
        const otherTotal = others.reduce((sum, c) => sum + (c.amount || 0), 0)
        const otherBar = {
          id: 'others',
          label: 'Others',
          amount: parseFloat(otherTotal.toFixed(2)),
          children: others.length ? others : [{ id: 'others', label: 'Others', amount: 0 }],
        }

        processed = [...topFour, otherBar]
      }

      categoryTree.value = processed
      emit(
        'categories-change',
        categoryTree.value.flatMap((cat) => (cat.children || []).map((child) => String(child.id))),
      )
      updateSummary()
      await renderChart()
    }
  } catch (err) {
    console.error('Error loading breakdown data:', err)
  }
}

function sumSelectedAmounts(nodes, selectedIds) {
  const sel = new Set((selectedIds || []).map((x) => String(x)))
  return (nodes || []).reduce((sum, n) => {
    let subtotal = 0
    if (sel.has(String(n.id))) {
      subtotal += n.amount
    }
    subtotal += sumSelectedAmounts(n.children || [], Array.from(sel))
    return sum + subtotal
  }, 0)
}

function updateSummary() {
  const total = sumSelectedAmounts(categoryTree.value, selectedCategoryIds.value)
  emit('summary-change', {
    total,
    startDate: startDate.value,
    endDate: endDate.value,
  })
}

// --- Reactivity ---
onMounted(fetchData)

// Refetch data when range or grouping changes
watch([startDate, endDate, groupOthers, breakdownType], debounce(fetchData, 200))

// When selectedCategoryIds changes, update summary and re-render
watch(
  selectedCategoryIds,
  debounce(async () => {
    updateSummary()
    await renderChart()
  }, 200),
  { deep: true },
)

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }
  const canvasEl = chartCanvas.value
  if (canvasEl && Chart.getChart) {
    const existing = Chart.getChart(canvasEl)
    if (existing) existing.destroy()
  }
})
</script>
