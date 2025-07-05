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
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { debounce } from 'lodash-es'
import { Chart } from 'chart.js/auto'
import { fetchCategoryBreakdownTree } from '@/api/charts'
import { fetchCategoryTree } from '@/api/categories'
import GroupedCategoryDropdown from '@/components/ui/GroupedCategoryDropdown.vue'

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

// ---- FIXED LOGIC ----

// Just use the root nodes as parent categories
const parentCategories = computed(() => fullCategoryTree.value || [])

// For the dropdown
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

// --- Default select top 5 parents by amount (from breakdown tree) ---
// Only set the default ONCE per load
const defaultSet = ref(false);

watch(categoryTree, () => {
  if (!defaultSet.value && categoryTree.value.length) {
    // Always use the order from your breakdown API (categoryTree), which has .amount
    selectedCategoryIds.value = categoryTree.value
      .slice(0, 5)
      .sort((a, b) => (b.amount || 0) - (a.amount || 0))
      .map(cat => cat.id)
    defaultSet.value = true
    // renderChart will be called after fetchData, not here!
  }
})

function onCategoryFilter(val) {
  // Only allow selecting parents that exist in the dropdown
  const allowed = parentCategories.value.map(c => c.id)
  const asArray = Array.isArray(val) ? val : (val ? [val] : [])
  selectedCategoryIds.value = asArray.filter((id, i, arr) => allowed.includes(id) && arr.indexOf(id) === i)
  renderChart()
}

// Fetch all categories for dropdown
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

// Fetch chart breakdown data
async function fetchData() {
  try {
    defaultSet.value = false; // Reset so watcher runs after data load
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

// Only show parent categories as bars, based on selected ids
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
@reference "../../assets/css/main.css";

.dropdown-menu {
  @apply absolute bg-[var(--themed-bg)] border border-[var(--divider)] p-2 flex flex-col gap-1 max-h-80 overflow-y-auto z-30 min-w-[270px] shadow;
}
</style>
