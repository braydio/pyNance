<!--
  SpendingInsights.vue
  Displays top merchants and spending categories with mini trend charts.
-->
<template>
  <div
    class="md:col-span-1 bg-[var(--color-bg-sec)] rounded-2xl shadow-xl border-2 border-[var(--color-accent-magenta)] p-6 flex flex-col gap-4"
  >
    <h2 class="text-xl font-bold text-[var(--color-accent-magenta)]">Spending Insights</h2>
    <div class="flex flex-col gap-6">
      <section>
        <h3 class="font-semibold mb-2">Quick Signals</h3>
        <div class="grid grid-cols-2 gap-3">
          <div
            class="p-3 rounded-lg border border-[var(--color-accent-green)]/40 bg-[var(--color-bg-dark)]"
          >
            <div class="text-xs text-[var(--color-text-muted)]">Rising Merchant</div>
            <div class="font-semibold truncate">{{ risingMerchant?.name || '—' }}</div>
            <div
              class="text-xs"
              :class="
                risingMerchantDelta >= 0
                  ? 'text-[var(--color-accent-green)]'
                  : 'text-[var(--color-accent-red)]'
              "
            >
              {{ risingMerchantDelta >= 0 ? '+' : '' }}{{ (risingMerchantDelta * 100).toFixed(0) }}%
            </div>
          </div>
          <div
            class="p-3 rounded-lg border border-[var(--color-accent-yellow)]/40 bg-[var(--color-bg-dark)]"
          >
            <div class="text-xs text-[var(--color-text-muted)]">Rising Category</div>
            <div class="font-semibold truncate">{{ risingCategory?.name || '—' }}</div>
            <div
              class="text-xs"
              :class="
                risingCategoryDelta >= 0
                  ? 'text-[var(--color-accent-green)]'
                  : 'text-[var(--color-accent-red)]'
              "
            >
              {{ risingCategoryDelta >= 0 ? '+' : '' }}{{ (risingCategoryDelta * 100).toFixed(0) }}%
            </div>
          </div>
        </div>
      </section>
      <section>
        <h3 class="font-semibold mb-2">Top Merchants</h3>
        <div class="flex flex-col gap-2 overflow-x-scroll">
          <div v-for="m in topMerchants" :key="m.name" class="flex items-center gap-2">
            <span class="flex-1 truncate whitespace-nowrap">{{ m.name }}</span>
            <span class="text-sm text-muted whitespace-nowrap">{{ formatCurrency(m.total) }}</span>
            <Line
              v-if="m.trend && m.trend.length"
              :data="sparklineData(m.trend)"
              :options="chartOptions"
              class="w-16 h-6"
            />
          </div>
        </div>
      </section>
      <section>
        <h3 class="font-semibold mb-2">Top Categories</h3>
        <div class="flex flex-col gap-2 overflow-x-scroll">
          <div v-for="c in topCategories" :key="c.name" class="flex items-center gap-2">
            <span class="flex-1 truncate whitespace-nowrap">{{ c.name }}</span>
            <span class="text-sm text-muted whitespace-nowrap">{{ formatCurrency(c.total) }}</span>
            <Line
              v-if="c.trend && c.trend.length"
              :data="sparklineData(c.trend)"
              :options="chartOptions"
              class="w-16 h-6"
            />
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart, LineElement, PointElement, LinearScale, CategoryScale } from 'chart.js'
import { fetchTopMerchants, fetchTopCategories } from '@/api/transactions'
import { formatCurrency } from '@/utils/currency'

Chart.register(LineElement, PointElement, LinearScale, CategoryScale)

const topMerchants = ref([])
const topCategories = ref([])

const chartOptions = {
  responsive: false,
  maintainAspectRatio: false,
  scales: {
    x: { display: false },
    y: { display: false },
  },
  elements: {
    line: { borderWidth: 1, tension: 0.3 },
    point: { radius: 0 },
  },
  plugins: {
    legend: { display: false },
    tooltip: { enabled: false },
  },
}

function sparklineData(trend = []) {
  return {
    labels: trend.map((_, i) => i),
    datasets: [
      {
        data: trend,
        borderColor: 'var(--color-accent-magenta)',
        fill: false,
      },
    ],
  }
}

onMounted(async () => {
  try {
    const [merchants, categories] = await Promise.all([
      fetchTopMerchants().catch(() => []),
      fetchTopCategories().catch(() => []),
    ])
    topMerchants.value = Array.isArray(merchants) ? merchants : []
    topCategories.value = Array.isArray(categories) ? categories : []
  } catch (err) {
    console.error('Failed to load spending insights:', err)
    topMerchants.value = []
    topCategories.value = []
  }
})

// Simple trend slope-based signals
const risingMerchant = computed(() => {
  return (
    [...(topMerchants.value || [])]
      .filter((m) => Array.isArray(m.trend) && m.trend.length > 2)
      .map((m) => ({ m, slope: slope(m.trend) }))
      .sort((a, b) => b.slope - a.slope)[0]?.m || null
  )
})
const risingCategory = computed(() => {
  return (
    [...(topCategories.value || [])]
      .filter((c) => Array.isArray(c.trend) && c.trend.length > 2)
      .map((c) => ({ c, slope: slope(c.trend) }))
      .sort((a, b) => b.slope - a.slope)[0]?.c || null
  )
})
const risingMerchantDelta = computed(() =>
  risingMerchant.value ? slopePct(risingMerchant.value.trend) : 0,
)
const risingCategoryDelta = computed(() =>
  risingCategory.value ? slopePct(risingCategory.value.trend) : 0,
)

function slope(arr = []) {
  const n = arr.length
  if (n < 2) return 0
  const x = Array.from({ length: n }, (_, i) => i)
  const sumX = x.reduce((a, b) => a + b, 0)
  const sumY = arr.reduce((a, b) => a + b, 0)
  const sumXY = x.reduce((s, xi, i) => s + xi * arr[i], 0)
  const sumXX = x.reduce((s, xi) => s + xi * xi, 0)
  return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
}
function slopePct(arr = []) {
  const n = arr.length
  if (n < 2) return 0
  const first = arr[0] || 1
  const last = arr[n - 1] || 1
  if (first === 0) return 0
  return (last - first) / Math.abs(first)
}
</script>
