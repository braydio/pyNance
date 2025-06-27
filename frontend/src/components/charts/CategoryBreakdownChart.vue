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
        <button
          class="legend-toggle px-2 py-1 text-xs rounded bg-[var(--color-accent-yellow)] text-[var(--color-bg-dark)] transition-colors"
          @click="showLegend = !showLegend">
          {{ showLegend ? 'Hide Legend' : 'Show Legend' }}
        </button>
      </div>
      <div
        class="chart-summary bg-[var(--color-bg-secondary)] px-3 py-2 rounded font-mono text-[var(--color-text-muted)] z-10 text-right border-2 border-[var(--divider)] shadow backdrop-blur-sm transition ml-auto">
        <span>Total: {{ totalSpending.toLocaleString() }}</span>
      </div>
    </div>
    <div v-if="showLegend"
      class="legend flex flex-wrap gap-1 mb-2 text-sm text-[var(--color-text-light)] transition-all duration-300">
      <FuzzyDropdown :options="flattenedCategories" :modelValue="selectedCategoryId"
        @update:modelValue="val => selectedCategoryId = val" placeholder="Filter by category..." class="w-64" />
    </div>
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
const chartData = ref([])
const categoryTree = ref([])
const selectedCategoryId = ref(null)
const showLegend = ref(true)

const today = new Date()
const endDate = ref(today.toISOString().slice(0, 10))
const startDate = ref(
  new Date(today.setDate(today.getDate() - 30)).toISOString().slice(0, 10)
)

const flattenedCategories = computed(() => flattenTree(categoryTree.value))
const totalSpending = computed(() => sumAmounts(chartData.value))

onMounted(fetchData)

watch(
  [startDate, endDate, selectedCategoryId],
  debounce(fetchData, 300),
  { immediate: false }
)

async function fetchData() {
  try {
    const response = await fetchCategoryBreakdownTree({
      start_date: startDate.value,
      end_date: endDate.value,
      ...(selectedCategoryId.value && { category_id: selectedCategoryId.value }),
    })

    if (response.status === 'success') {
      chartData.value = response.data || []
      categoryTree.value = response.data || []
      await nextTick()
      renderChart()
    }
  } catch (err) {
    console.error('Error loading breakdown data:', err)
  }
}

function flattenTree(tree) {
  const flattened = []

  function traverse(node, depth = 0) {
    flattened.push({
      id: node.id,
      name: `${'— '.repeat(depth)}${node.label}`,
    })
    if (Array.isArray(node.children)) {
      node.children.forEach(child => traverse(child, depth + 1))
    }
  }

  tree.forEach(root => traverse(root))
  return flattened
}

function sumAmounts(nodes) {
  return nodes.reduce((sum, n) => {
    const subtotal = n.amount + sumAmounts(n.children || [])
    return sum + subtotal
  }, 0)
}

function extractLeafNodes(nodes) {
  const result = []
  function collect(node) {
    if (!node.children || node.children.length === 0) {
      result.push(node)
    } else {
      node.children.forEach(collect)
    }
  }
  nodes.forEach(collect)
  return result
}

function renderChart() {
  const ctx = chartCanvas.value?.getContext('2d')
  if (!ctx) return

  if (chartInstance.value) chartInstance.value.destroy()

  const leafNodes = extractLeafNodes(chartData.value)
  const labels = leafNodes.map(n => n.label)
  const data = leafNodes.map(n => n.amount)

  chartInstance.value = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Spending',
          data,
          backgroundColor: '#a78bfa',
          borderColor: '#7c3aed',
          borderWidth: 1,
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
/* Only theme or special effect styles here */
.legend {
  /* Can stay for spacing, but remove size/layout from here */
}
</style>
