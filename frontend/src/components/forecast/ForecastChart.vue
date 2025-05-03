<script setup>
import { ref, watch, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import { useForecastEngineMock } from '@/composables/useForecastEngine'
import { mockRecurringTransactions, mockAccountHistory } from '@/mocks/forecastMockData'

Chart.register(...registerables)

const props = defineProps({
  forecastItems: {
    type: Array,
    default: () => [],
  },
  viewType: {
    type: String,
    default: 'Month',
  },
  manualIncome: {
    type: Number,
    default: 0,
  },
  liabilityRate: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['update:viewType'])
const chartCanvas = ref(null)
let chartInstance = null

const { labels, forecastLine, actualLine } = useForecastEngineMock(
  props.viewType,
  mockRecurringTransactions,
  mockAccountHistory,
  props.manualIncome,
  props.liabilityRate
)

function toggleView() {
  emit('update:viewType', props.viewType === 'Month' ? 'Year' : 'Month')
}

function renderChart() {
  if (!chartCanvas.value) return
  const ctx = chartCanvas.value.getContext('2d')
  if (chartInstance) chartInstance.destroy()

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.value,
      datasets: [
        {
          label: 'Forecast',
          data: forecastLine.value,
          borderColor: '#3B82F6',
          tension: 0.3,
        },
        {
          label: 'Actual',
          data: actualLine.value,
          borderColor: '#10B981',
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      scales: { y: { beginAtZero: false } },
    },
  })
}

onMounted(renderChart)
watch(() => [labels.value, forecastLine.value, actualLine.value], renderChart)
</script>
