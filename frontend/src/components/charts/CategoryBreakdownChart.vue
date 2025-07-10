<template>
  <div class="relative w-full h-[400px] bg-[var(--theme-bg)] rounded-xl overflow-hidden border border-[var(--divider)]">
    <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
  </div>
</template>


<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree } from '@/api/charts'

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  selectedCategoryIds: { type: Array, default: () => [] }
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

const totalSpending = computed(() => sumAmounts(categoryTree.value))

function sumAmounts(nodes) {
  return (nodes || []).reduce((sum, n) => {
    const subtotal = n.amount + sumAmounts(n.children || [])
    return sum + subtotal
  }, 0)
}

function extractBars(tree, selectedIds = []) {
  let bars
  if (selectedIds && selectedIds.length) {
    bars = tree.filter(node => selectedIds.includes(node.id))
  } else {
    bars = tree
  }
  if (!bars.length && tree.length) {
    bars = tree
  }
  return {
    labels: bars.map(b => b.label),
    data: bars.map(b => b.amount),
    colors: bars.map((b, idx) => getGroupColor(idx)),
  }
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
    const label = chartInstance.value.data.labels[index]
    emit('bar-click', label)
  }
}

async function renderChart() {
  await nextTick()
  const canvasEl = chartCanvas.value
  if (!canvasEl) return
  destroyPreviousChart(canvasEl)
  const ctx = canvasEl.getContext('2d')
  if (!ctx) return

  const { labels, data, colors } = extractBars(categoryTree.value, props.selectedCategoryIds)

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : [' '],
      datasets: [
        {
          label: 'Spending',
          data: data.length ? data : [0],
          backgroundColor: colors.length ? colors : [getGroupColor(0)],
          borderColor: colors.length ? colors : [getGroupColor(0)],
          borderWidth: 2,
          borderSkipped: false,
          barPercentage: 0.9,
          categoryPercentage: 0.8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20, bottom: 20 } },
      onClick: handleBarClick,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: context => {
              const val = context.raw ?? 0
              return val < 0
                ? `($${Math.abs(val).toLocaleString()})`
                : `$${val.toLocaleString()}`
            },
          },
          backgroundColor: getStyle('--theme-bg'),
          titleColor: getStyle('--color-accent-yellow'),
          bodyColor: getStyle('--color-text-light'),
          borderColor: getStyle('--color-accent-yellow'),
          borderWidth: 1,
        },
      },
      scales: {
        x: {
          display: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
        },
        y: {
          display: true,
          beginAtZero: true,
          grid: { display: true, color: getStyle('--divider') },
          ticks: {
            callback: value => value < 0
              ? `($${Math.abs(value).toLocaleString()})`
              : `$${value.toLocaleString()}`,
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
      categoryTree.value = response.data || []
      emit('categories-change', categoryTree.value.map(cat => cat.id))
      emit('summary-change', {
        total: totalSpending.value,
        startDate: props.startDate,
        endDate: props.endDate,
      })
      await renderChart()
    }
  } catch (err) {
    console.error('Error loading breakdown data:', err)
  }
}

watch(
  () => [props.startDate, props.endDate, props.selectedCategoryIds],
  debounce(fetchData, 200),
  { immediate: true }
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
