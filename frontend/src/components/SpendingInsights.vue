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
import { ref, onMounted } from 'vue'
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
  topMerchants.value = await fetchTopMerchants()
  topCategories.value = await fetchTopCategories()
})
</script>
