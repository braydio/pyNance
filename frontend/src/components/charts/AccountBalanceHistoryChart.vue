<template>
  <div class="account-balance-history-chart" style="height: 400px">
    <Transition name="fade-slide" mode="out-in">
      <canvas
        v-if="hasData"
        :key="transitionKey"
        ref="chartCanvas"
        style="width: 100%; height: 100%"
      ></canvas>
      <p v-else class="text-center text-sm" style="color: var(--color-text-muted)">
        No history available for this period
      </p>
    </Transition>
  </div>
</template>

<script setup>
import { Chart } from 'chart.js/auto'
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { formatAmount } from '@/utils/format'

// AccountBalanceHistoryChart.vue
// Displays a line chart of account balances over time. Accepts historyData and
// selectedRange props and animates when data or range changes.
const props = defineProps({
  historyData: {
    type: Array,
    default: () => [],
  },
  selectedRange: {
    type: String,
    default: '',
  },
})

const chartInstance = ref(null)
const chartCanvas = ref(null)
const transitionKey = ref(0)

const hasData = computed(() => (props.historyData || []).length > 0)

/**
 * Render the Chart.js instance using current historyData.
 * Destroys any existing chart before creating a new one.
 */
async function renderChart() {
  await nextTick()

  if (chartInstance.value) {
    chartInstance.value.destroy()
    chartInstance.value = null
  }

  if (!hasData.value) return

  const labels = props.historyData.map((b) => b.date)
  const values = props.historyData.map((b) => b.balance)

  const ctx = chartCanvas.value.getContext('2d')
  chartInstance.value = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Balance',
          data: values,
          borderColor: getStyle('--color-accent-green'),
          backgroundColor: 'transparent',
          fill: false,
          tension: 0.3,
          pointRadius: 0, // smooth line
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          enabled: true,
          backgroundColor: getStyle('--theme-bg'),
          borderColor: getStyle('--divider'),
          borderWidth: 1,
          callbacks: {
            label: (ctx) => `Balance: ${formatAmount(ctx.raw)}`,
          },
        },
        legend: {
          display: true,
          labels: { color: getStyle('--color-text-muted') },
        },
      },
      scales: {
        y: {
          grid: { color: getStyle('--divider') },
          ticks: {
            callback: (value) => formatAmount(value),
            color: getStyle('--color-text-muted'),
          },
        },
        x: {
          grid: { color: getStyle('--divider') },
          ticks: {
            maxRotation: 45,
            minRotation: 0,
            color: getStyle('--color-text-muted'),
          },
        },
      },
    },
  })
}

function triggerRender() {
  transitionKey.value++
  renderChart()
}

onMounted(() => renderChart())
onUnmounted(() => {
  if (chartInstance.value) chartInstance.value.destroy()
})
watch(() => props.historyData, triggerRender, { deep: true })
watch(() => props.selectedRange, triggerRender)

function getStyle(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
