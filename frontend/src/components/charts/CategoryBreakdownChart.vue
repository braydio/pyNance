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

    <!-- Multi-select dropdown filter -->
    <FuzzyDropdown :options="flattenedCategories" :modelValue="selectedCategoryIds"
      @update:modelValue="onCategoryFilter" placeholder="Filter by main/subcategory (multi)…" class="w-80 mb-3"
      :max="50" />

    <div class="relative w-full h-[400px]">
      <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import FuzzyDropdown from '@/components/ui/FuzzyDropdown.vue'
import { fetchCategoryBreakdownTree } from '@/api/charts'

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryTree = ref([])
const selectedCategoryIds = ref([])

const today = new Date()
const endDate = ref(today.toISOString().slice(0, 10))
const startDate = ref(
  new Date(today.setDate(today.getDate() - 30)).toISOString().slice(0, 10)
)

const totalSpending = computed(() => sumAmounts(categoryTree.value))

const groupColors = [
  '#a78bfa', '#5db073', '#fbbf24', '#a43e5c', '#3b82f6',
  '#eab308', '#f472b6', '#60a5fa', '#e11d48', '#38ffd4'
]
function getGroupColor(idx) {
  return groupColors[idx % groupColors.length]
}

// Fetch & data
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

function sumAmounts(nodes) {
  return (nodes || []).reduce((sum, n) => {
    const subtotal = n.amount + sumAmounts(n.children || [])
    return sum + subtotal
  }, 0)
}

// -- FLATTENING FOR SELECTOR --
const flattenedCategories = computed(() => {
  const flat = []
  function traverse(node, parentLabel = '') {
    // Main/root
    if (!node.parent_id) {
      flat.push({
        id: node.id,
        name: node.label,
        isRoot: true,
      })
      if (node.children) {
        node.children.forEach(child =>
          traverse(child, node.label)
        )
      }
    } else {
      // Subcategory
      flat.push({
        id: node.id,
        name: parentLabel ? `${parentLabel}: ${node.label}` : node.label,
        isRoot: false,
      })
      if (node.children) {
        node.children.forEach(child =>
          traverse(child, parentLabel)
        )
      }
    }
  }
  (categoryTree.value || []).forEach(root => traverse(root))
  return flat
})

// -- FILTER --
function onCategoryFilter(val) {
  selectedCategoryIds.value = Array.isArray(val) ? val : (val ? [val] : [])
  renderChart()
}

// -- CHART --
function extractBars(tree, selectedIds = []) {
  if (Array.isArray(selectedIds) && selectedIds.length) {
    // Find selected nodes (roots/subcats)
    const found = []
    function findNodes(nodes) {
      for (const node of nodes) {
        if (selectedIds.includes(node.id) || selectedIds.includes(String(node.id))) {
          found.push(node)
        }
        if (node.children) findNodes(node.children)
      }
    }
    findNodes(tree)
    // Group by root color
    const bars = []
    for (const node of found) {
      // Find root group index for color
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
  // No filter: just main cats as bars
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
/* Simple, chart-focused, no legend */
</style>
