<template>
  <div
    class="category-breakdown-chart bg-[var(--color-bg-sec)] p-4 rounded-2xl shadow w-full border border-[var(--divider)] relative">
    <ChartWidgetTopBar>
      <template #icon>
        <!-- Use any relevant SVG icon you want here -->
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-[var(--color-accent-mint)]" fill="none"
          viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M3 10h4V3H3v7zm0 0v11h4v-4h6v4h4V3h-4v7H3zm7 4h2v2h-2v-2z" />
        </svg>
      </template>
      <template #title>
        Spending by Category
      </template>
      <template #controls>
        <input type="date" v-model="startDate"
          class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-mint)]" />
        <input type="date" v-model="endDate"
          class="date-picker px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)] focus:ring-2 focus:ring-[var(--color-accent-mint)]" />
      </template>
      <template #summary>
        <span class="text-sm">Total:</span>
        <span class="font-bold text-lg text-[var(--color-accent-mint)]">${{ totalSpending.toLocaleString() }}</span>
      </template>
    </ChartWidgetTopBar>

    <GroupedCategoryDropdown :groups="categoryGroups" :modelValue="selectedCategoryIds"
      @update:modelValue="onCategoryFilter" class="w-96 mb-4" />

    <div
      class="relative w-full h-[400px] bg-[var(--theme-bg)] rounded-xl overflow-hidden border border-[var(--divider)]">
      <canvas ref="chartCanvas" class="absolute inset-0 w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree } from '@/api/charts'
import { fetchCategoryTree } from '@/api/categories'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'
import ChartWidgetTopBar from '@/components/ui/ChartWidgetTopBar.vue'

const emit = defineEmits(['bar-click'])

const chartCanvas = ref(null)
const chartInstance = ref(null)
const categoryTree = ref([])
const fullCategoryTree = ref([])
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

// Retrieve a CSS custom property value
function getStyle(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
}

const parentCategories = computed(() => fullCategoryTree.value || [])

const categoryGroups = computed(() =>
  (parentCategories.value || [])
    .map(root => ({
      id: root.id,
      label: root.label,
      children: (root.children || []).map(c => ({
        id: c.id,
        label: c.label ?? c.name,
      })),
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
)

const defaultSet = ref(false);

watch(categoryTree, () => {
  if (!defaultSet.value && categoryTree.value.length) {
    selectedCategoryIds.value = categoryTree.value
      .slice(0, 5)
      .sort((a, b) => (b.amount || 0) - (a.amount || 0))
      .map(cat => cat.id)
    defaultSet.value = true
  }
})

function onCategoryFilter(val) {
  const allowed = parentCategories.value.map(c => c.id)
  const asArray = Array.isArray(val) ? val : (val ? [val] : [])
  selectedCategoryIds.value = asArray.filter((id, i, arr) => allowed.includes(id) && arr.indexOf(id) === i)
  renderChart()
}

async function loadFullTree() {
  try {
    const res = await fetchCategoryTree()
    if (res.status === 'success') {
      fullCategoryTree.value = res.data || []
    }
  } catch (err) {
    console.error('Error loading category tree:', err)
  }
}

async function fetchData() {
  try {
    defaultSet.value = false;
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

function extractBars(tree, selectedIds = []) {
  let bars
  if (selectedIds && selectedIds.length) {
    bars = tree.filter(node => selectedIds.includes(node.id))
  } else {
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
      layout: { padding: { top: 20, bottom: 20 } },
      onClick: handleBarClick,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: context => `$${context.raw.toLocaleString()}`,
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
          ticks: {
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
          grid: { color: getStyle('--divider') },
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: value => `$${value}`,
            color: getStyle('--color-text-muted'),
            font: { family: "'Fira Code', monospace", size: 14 },
          },
          grid: { color: getStyle('--divider') },
        },
      },
    },
  })
}

onMounted(async () => {
  await loadFullTree()
  await fetchData()
})
watch(
  [startDate, endDate],
  debounce(fetchData, 300),
  { immediate: false }
)
</script>

<style scoped>
@import "../../assets/css/main.css";

.category-breakdown-chart .relative {
  background: var(--theme-bg);
  border-radius: 1rem;
  box-shadow: 0 1px 8px 0 rgb(30 41 59 / 10%);
}
</style>
