<template>
  <div
    class="relative w-full max-w-full h-[400px] bg-[var(--theme-bg)] rounded-xl overflow-hidden border border-[var(--divider)]"
  >
    <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
    <div
      v-if="showEmptyState"
      class="absolute inset-0 flex items-center justify-center text-center px-6 text-[var(--color-text-muted)]"
    >
      Your chart has no items to display. A chart needs items to display for it to feel satisfied
      and complete.
    </div>
  </div>
</template>

<script setup>
// CategoryBreakdownChart.vue
// Displays a stacked bar chart of spending. By default, only the top four
// parent categories are shown individually with the rest grouped into an
// "Other" bar. Set `groupOthers` to `false` to show all categories.
import { ref, watch, nextTick, onMounted, onUnmounted, toRefs, computed } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree } from '@/api/charts'
import { formatAmount } from '@/utils/format'
import { getAccentColor } from '@/utils/colors'

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  selectedCategoryIds: { type: Array, default: () => [] },
  groupOthers: { type: Boolean, default: true },
})

const { startDate, endDate, selectedCategoryIds, groupOthers } = toRefs(props)

const emit = defineEmits(['bar-click', 'summary-change', 'categories-change'])

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryTree = ref([])
const showEmptyState = computed(() => (selectedCategoryIds.value?.length || 0) === 0)

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

function extractStackedBarData(tree, selectedIds = []) {
  // Only include parents that have at least one selected child
  const sel = new Set((selectedIds || []).map((x) => String(x)))
  const parents = tree.filter((node) => node.children?.some((child) => sel.has(String(child.id))))
  const labels = parents.map((p) => p.label)

  // Collect unique child IDs for selected categories across all parents
  const childIdSet = new Set()
  parents.forEach((p) =>
    (p.children || []).forEach((c) => {
      if (sel.has(String(c.id))) childIdSet.add(String(c.id))
    }),
  )
  const allChildIds = Array.from(childIdSet)

  // Map each child ID to its label for display
  function labelForId(id) {
    for (const p of parents) {
      const match = (p.children || []).find((c) => String(c.id) === String(id))
      if (match) return match.label
    }
    return ''
  }

  const datasets = allChildIds.map((childId, colorIdx) => ({
    label: labelForId(childId),
    data: parents.map((p) => {
      const child = (p.children || []).find((c) => String(c.id) === String(childId))
      return child ? child.amount : 0
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

  // If nothing is selected, do not render a chart; show the empty-state overlay instead
  if (showEmptyState.value) {
    return
  }

  const { labels, datasets } = extractStackedBarData(categoryTree.value, selectedCategoryIds.value)

  // If there are no datasets to show (e.g., selected IDs do not match current data),
  // avoid rendering an empty chart.
  if (!datasets.length || !labels.length) {
    return
  }

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: { top: 20, bottom: 20 } },
      plugins: {
        legend: {
          display: true,
          labels: {
            color: getStyle('--color-text-muted'),
            // Hide any legend item with text 'Debit'
            filter: (legendItem) => legendItem.text !== 'Debit',
          },
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          displayColors: false,
          filter: (tooltipItem) => tooltipItem.datasetIndex === 0,
          callbacks: {
            // No title; axis label already shows parent
            title: () => '',
            // Show total first in the body
            beforeBody: (items) => {
              const label = items?.[0]?.label || ''
              const node = categoryTree.value.find((cat) => cat.label === label)
              const sel = new Set((selectedCategoryIds.value || []).map((x) => String(x)))
              const children = (node?.children || []).filter((c) => sel.has(String(c.id)))
              const total = children.reduce((sum, c) => sum + (c.amount || 0), 0)
              return [`Total: ${formatAmount(total)}`]
            },
            // Body lists top 5 child categories with amounts
            label: (context) => {
              const label = context.label || ''
              const node = categoryTree.value.find((cat) => cat.label === label)
              const sel = new Set((selectedCategoryIds.value || []).map((x) => String(x)))
              const children = (node?.children || [])
                .filter((c) => sel.has(String(c.id)))
                .sort((a, b) => (b.amount || 0) - (a.amount || 0))
                .slice(0, 5)
              if (!children.length) return []
              return children.map((c) => `${c.label}: ${formatAmount(c.amount || 0)}`)
            },
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
          const label = chartInstance.value.data.labels[index]
          const node = categoryTree.value.find((cat) => cat.label === label)
          // Only emit IDs for categories currently selected by the user
          const sel = new Set((selectedCategoryIds.value || []).map((x) => String(x)))
          const ids = (node?.children || [])
            .filter((c) => sel.has(String(c.id)))
            .map((c) => String(c.id))
          emit('bar-click', { label, ids })
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
            callback: (value) => formatAmount(value),
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
      start_date: startDate.value,
      end_date: endDate.value,
      top_n: 50,
    })
    if (response.status === 'success') {
      const raw = response.data || []
      let processed = raw
      if (groupOthers.value && raw.length > 4) {
        const topFour = raw.slice(0, 4)
        const others = raw.slice(4)
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
watch([startDate, endDate, groupOthers], debounce(fetchData, 200))

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
