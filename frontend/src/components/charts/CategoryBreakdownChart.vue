<template>
  <div class="relative w-full h-[400px] bg-[var(--theme-bg)] rounded-xl overflow-hidden border border-[var(--divider)]">
    <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
  </div>
</template>

<script setup>
// CategoryBreakdownChart.vue
// Displays a stacked bar chart of spending. By default, only the top four
// parent categories are shown individually with the rest grouped into an
// "Other" bar. Set `groupOthers` to `false` to show all categories.
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree } from '@/api/charts'
import { formatAmount } from "@/utils/format"

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  selectedCategoryIds: { type: Array, default: () => [] },
  groupOthers: { type: Boolean, default: true }
})

const emit = defineEmits(['bar-click', 'summary-change', 'categories-change'])

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryTree = ref([])

const groupColors = [
  '#a78bfa', '#5db073', '#fbbf24', '#a43e5c', '#3b82f6',
  '#eab308', '#f472b6', '#60a5fa', '#e11d48', '#38ffd4'
]
function getGroupColor(idx) {
  return groupColors[idx % groupColors.length]
}

function destroyPreviousChart(canvasEl) {
  if (!canvasEl) return
  const prev = Chart.getChart(canvasEl)
  if (prev) prev.destroy()
  chartInstance.value = null
}

function getStyle(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
}

function extractStackedBarData(tree, selectedIds = []) {
  // Show parent only if any of its children is selected
  const parents = tree.filter(
    node =>
      node.children && node.children.some(child => selectedIds.includes(child.id))
  )
  const labels = parents.map(p => p.label)
  // All visible children (segments)
  const allChildLabels = [
    ...new Set(
      parents.flatMap(p =>
        (p.children || []).filter(c => selectedIds.includes(c.id)).map(c => c.label)
      )
    )
  ]
  // Datasets: Only selected children
  const datasets = allChildLabels.map((childLabel, colorIdx) => ({
    label: childLabel,
    data: parents.map(p => {
      const child = (p.children || []).find(c => c.label === childLabel)
      return (child && selectedIds.includes(child.id)) ? child.amount : 0
    }),
    backgroundColor: getGroupColor(colorIdx),
    borderWidth: 2,
    borderSkipped: false,
    barPercentage: 0.9,
    categoryPercentage: 0.8,
  }))
  return { labels, datasets }
}

async function renderChart() {
  await nextTick()
  const canvasEl = chartCanvas.value
  if (!canvasEl) return
  destroyPreviousChart(canvasEl)
  const ctx = canvasEl.getContext('2d')
  if (!ctx) return

  const { labels, datasets } = extractStackedBarData(categoryTree.value, props.selectedCategoryIds)

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : [' '],
      datasets: datasets.length ? datasets : [{
        label: 'Spending',
        data: [0],
        backgroundColor: getGroupColor(0),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20, bottom: 20 } },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: context => {
              const val = context.raw ?? 0
              return `${context.dataset.label}: ${formatAmount(val)}`
            }
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
          evt, 'nearest', { intersect: true }, false
        )
        if (points.length) {
          const index = points[0].index
          const label = chartInstance.value.data.labels[index]
          emit('bar-click', label)
        }
      },
      scales: {
        x: {
          stacked: true,
          display: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
        },
        y: {
          stacked: true,
          display: true,
          beginAtZero: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            callback: value => formatAmount(value),
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
        },
      },
    },
  })
}

async function fetchData() {
  try {
    const response = await fetchCategoryBreakdownTree({
      start_date: props.startDate,
      end_date: props.endDate,
      top_n: 50,
    })
    if (response.status === 'success') {
      const raw = response.data || []
      let processed = raw
      if (props.groupOthers && raw.length > 4) {
        const topFour = raw.slice(0, 4)
        const others = raw.slice(4)
        const otherTotal = others.reduce((sum, c) => sum + (c.amount || 0), 0)
        const otherBar = {
          id: 'other',
          label: 'Other',
          amount: parseFloat(otherTotal.toFixed(2)),
          children: [
            { id: 'other', label: 'Other', amount: parseFloat(otherTotal.toFixed(2)) }
          ]
        }
        processed = [...topFour, otherBar]
      }
      categoryTree.value = processed
      emit('categories-change', categoryTree.value.map(cat => cat.id))
      emit('summary-change', {
        total: sumAmounts(categoryTree.value),
        startDate: props.startDate,
        endDate: props.endDate,
      })
      await renderChart()
    }
  } catch (err) {
    console.error('Error loading breakdown data:', err)
  }
}

function sumAmounts(nodes) {
  return (nodes || []).reduce((sum, n) => {
    const subtotal = n.amount + sumAmounts(n.children || [])
    return sum + subtotal
  }, 0)
}

// --- Reactivity ---
onMounted(fetchData)

// Refetch data when range or grouping changes
watch(
  () => [props.startDate, props.endDate, props.groupOthers],
  debounce(fetchData, 200)
)

// Re-render when selected categories change
watch(
  () => props.selectedCategoryIds,
  debounce(renderChart, 200),
  { deep: true }
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
