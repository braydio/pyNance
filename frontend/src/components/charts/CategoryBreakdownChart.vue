<template>
  <div
    class="category-breakdown-chart bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)] relative">
    <div class="flex justify-between items-center flex-wrap gap-2 mb-2">
      <h2 class="text-xl font-semibold">Spending by Category</h2>
      <div class="flex gap-2 items-center">
        <input type="date" v-model="startDate"
          class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)]" />
        <input type="date" v-model="endDate"
          class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)]" />
      </div>
      <div
        class="chart-summary bg-[var(--color-bg-secondary)] px-3 py-2 rounded font-mono text-[var(--color-text-muted)] z-10 text-right border-2 border-[var(--divider)] shadow backdrop-blur-sm transition ml-auto">
        <span>Total: {{ totalSpending.toLocaleString() }}</span>
      </div>
    </div>

    <!-- Grouped Multi-select Dropdown Filter -->
    <GroupedCategoryDropdown :groups="categoryGroups" :modelValue="selectedCategoryIds"
      @update:modelValue="onCategoryFilter" class="w-96 mb-3" />

    <div class="relative w-full h-[400px]">
      <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
/**
 * CategoryBreakdownChart visualizes spending per category.
 * Emits a `bar-click` event when a bar is clicked.
 */
import { ref, computed, onMounted, watch, nextTick, defineEmits } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree } from '@/api/charts'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'

const emit = defineEmits(['bar-click'])

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryTree = ref([])
const selectedCategoryIds = ref([])

const today = new Date()
const endDate = ref(today.toISOString().slice(0, 10))
const startDate = ref(
  new Date(today.setDate(today.getDate() - 30)).toISOString().slice(0, 10)
)

const totalSpending = computed(() => sumRootAmounts(categoryTree.value))

const groupColors = [
  '#a78bfa', '#5db073', '#fbbf24', '#a43e5c', '#3b82f6',
  '#eab308', '#f472b6', '#60a5fa', '#e11d48', '#38ffd4'
]
function getGroupColor(idx) {
  return groupColors[idx % groupColors.length]
}

onMounted(fetchData)
watch(
  [startDate, endDate],
  debounce(fetchData, 300),
  { immediate: false }
)

async function fetchData() {
  try {
    const response = await fetchCategoryBreakdownTree({
      start_date: startDate.value,
      end_date: endDate.value,
      top_n: 50,
    })
    if (response.status === 'success') {
      categoryTree.value = response.data || []
      await nextTick()
      renderChart()
    }
  } catch (err) {
    console.error('Error loading breakdown data:', err)
  }
}

/**
 * Sum only root-level amounts from the category tree.
 * @param {Array<Object>} nodes - root nodes returned from the API
 * @returns {number} aggregated spending total
 */
function sumRootAmounts(nodes) {
  return (nodes || []).reduce((sum, n) => sum + (n.amount || 0), 0)
}

const categoryGroups = computed(() => {
  // [{id, label, children: [{id, label}]}]
  return (categoryTree.value || []).map(root => ({
    id: root.id,
    label: root.label,
    children: (root.children || []).map(child => ({
      id: child.id,
      label: child.label,
    })),
  }))
})

function onCategoryFilter(val) {
  selectedCategoryIds.value = Array.isArray(val) ? val : (val ? [val] : [])
  renderChart()
}

function extractBars(tree, selectedIds = []) {
  // Show only selected detailed cats if any, else all main cats
  if (selectedIds && selectedIds.length) {
    const found = []
    function findNodes(nodes) {
      for (const node of nodes) {
        if (selectedIds.includes(node.id)) {
          found.push(node)
        }
        if (node.children) findNodes(node.children)
      }
    }
    findNodes(tree)
    const bars = []
    for (const node of found) {
      let rootIdx = tree.findIndex(root => {
        if (root.id === node.id) return true
        function hasDescendant(n) {
          if (!n.children) return false
          for (const c of n.children) {
            if (c.id === node.id) return true
            if (hasDescendant(c)) return true
          }
          return false
        }
        return hasDescendant(root)
      })
      bars.push({
        label: node.label,
        amount: node.amount,
        color: getGroupColor(rootIdx),
      })
    }
    return {
      labels: bars.map(b => b.label),
      data: bars.map(b => b.amount),
      colors: bars.map(b => b.color),
    }
  }
  // No filter: main cats as bars
  const labels = []
  const data = []
  const colors = []
  tree.forEach((root, idx) => {
    labels.push(root.label)
    data.push(root.amount)
    colors.push(getGroupColor(idx))
  })
  return { labels, data, colors }
}

// Emit category label when a bar is clicked
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

function renderChart() {
  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return
  if (chartInstance.value) chartInstance.value.destroy()

  const { labels, data, colors } = extractBars(categoryTree.value, selectedCategoryIds.value)

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Spending',
          data,
          backgroundColor: colors,
          borderColor: colors,
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
      onClick: handleBarClick,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: context => `$${context.raw.toLocaleString()}`,
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: '#c4b5fd',
            font: { size: 14 },
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: value => `$${value}`,
            color: '#c4b5fd',
            font: { size: 14 },
          },
        },
      },
    },
  })
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.dropdown-menu {
  @apply absolute bg-[var(--themed-bg)] border border-[var(--divider)] p-2 flex flex-col gap-1 max-h-80 overflow-y-auto z-30 min-w-[270px] shadow;
}
</style>
