
<template>
  <div class="chart-container card">
   <div class="chart-title-row flex-between">
      <h2 class="heading-md">Net Assets vs. Liabilities</h2>
      <div class="chart-summary" v-if="metadata">
        <h4 class="text-accent">Current Totals</h4>
        <div class="summary-line assets">Assets: {{ formatCurrency(metadata.total_assets) }}</div>
        <div class="summary-line liabilities">Liabilities: {{ formatCurrency(metadata.total_liabilities, true) }}</div>
        <div class="summary-line net">Net: {{ formatCurrency(metadata.net_now) }}</div>
      </div>
    </div>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import axios from "axios";
import { ref, onMounted, nextTick } from "vue";
import { Chart } from "chart.js/auto";

export default {
  name: "NetAssetsChart",
  setup() {
    const chartCanvas = ref(null);
    const chartInstance = ref(null);
    const chartData = ref([]);
    const metadata = ref(null);

    const fetchData = async () => {
      try {
        const response = await axios.get("/api/charts/net_assets");
        if (response.data.status === "success") {
          chartData.value = response.data.data || [];
          metadata.value = response.data.metadata || null;
          updateChart();
        }
      } catch (error) {
        console.error("Error fetching net assets data:", error);
      }
    };

    const formatCurrency = (val) => {
      const number = parseFloat(val) || 0;
      return number < 0
        ? `($${Math.abs(number).toLocaleString()})`
        : `$${number.toLocaleString()}`;
    };

    const formatMMM = (dateString) => {
      const [yyyy, mm, dd] = dateString.split("-");
      return new Date(`${yyyy}-${mm}-${dd}`).toLocaleString("default", { month: "short" });
    };

    const updateChart = async () => {
      await nextTick();
      const canvasEl = chartCanvas.value;
      const ctx = canvasEl.getContext("2d");
      if (!canvasEl || !ctx) return;
      if (chartInstance.value) chartInstance.value.destroy();

      const labels = chartData.value.map(item => item.date);
      const assetsData = chartData.value.map(item => item.assets);
      const liabilitiesData = chartData.value.map(item => item.liabilities);
      const netData = chartData.value.map(item => item.net);

      chartInstance.value = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Assets",
              data: assetsData,
              borderColor: getComputedStyle(document.documentElement).getPropertyValue('--color-accent-ice').trim(),
              backgroundColor: "rgba(137, 220, 235, 0.15)",
              fill: false,
              tension: 0.1,
            },
            {
              label: "Liabilities",
              data: liabilitiesData,
              borderColor: getComputedStyle(document.documentElement).getPropertyValue('--bar-alert').trim(),
              backgroundColor: "rgba(251, 73, 52, 0.15)",
              fill: false,
              tension: 0.1,
            },
            {
              label: "Net",
              data: netData,
              borderColor: getComputedStyle(document.documentElement).getPropertyValue('--color-accent-yellow').trim(),
              backgroundColor: "rgba(250, 189, 47, 0.15)",
              fill: false,
              tension: 0.1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              ticks: {
                color: getComputedStyle(document.documentElement).getPropertyValue('--color-text-muted').trim(),
                callback: (value, index) => formatMMM(labels[index]),
              },
              grid: {
                color: getComputedStyle(document.documentElement).getPropertyValue('--divider').trim(),
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: getComputedStyle(document.documentElement).getPropertyValue('--color-text-muted').trim(),
                callback: (val) => {
                  const number = parseFloat(val);
                  return number < 0
                    ? `($${Math.abs(number).toLocaleString()})`
                    : `$${number.toLocaleString()}`;
                },
              },
              grid: {
                color: getComputedStyle(document.documentElement).getPropertyValue('--divider').trim(),
              },
            },
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => {
                  const label = context.dataset.label;
                  const val = context.raw;
                  return val < 0
                    ? `${label}: ($${Math.abs(val).toLocaleString()})`
                    : `${label}: $${val.toLocaleString()}`;
                },
                title: (context) => formatMMM(context[0].label),
              },
              backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--themed-bg').trim(),
              titleColor: getComputedStyle(document.documentElement).getPropertyValue('--color-accent-yellow').trim(),
              bodyColor: getComputedStyle(document.documentElement).getPropertyValue('--color-text-light').trim(),
              borderColor: getComputedStyle(document.documentElement).getPropertyValue('--color-accent-yellow').trim(),
              borderWidth: 1,
            },
            legend: {
              labels: {
                color: getComputedStyle(document.documentElement).getPropertyValue('--color-text-light').trim(),
              },
            },
          },
        },
      });
    };

    onMounted(() => fetchData());

    return {
      chartCanvas,
      metadata,
      formatCurrency,
    };
  },
};
</script>

<style scoped>
.chart-container {
  margin: 1rem;
  padding: 1rem;
  opacity: 0.95;
  position: relative;
  max-height: 400px;
  height: 100%;
}

.chart-title-row {
  margin-bottom: 0.75rem;
}

.chart-summary {
  background: var(--color-bg-secondary);
  padding: 0.75rem;
  border-radius: 6px;
  font-family: var(--font-mono, 'Fira Code', monospace);
  color: var(--color-text-muted);
  text-align: right;
  border: 1px solid var(--divider);
  box-shadow: 0 2px 6px var(--shadow);
}

.chart-summary h4 {
  margin-bottom: 0.5rem;
  font-size: 1rem;
  font-weight: bold;
  color: var(--color-accent-yellow);
}

.summary-line {
  margin: 0.25rem 0;
}

.summary-line.assets {
  color: var(--color-accent-ice);
}

.summary-line.liabilities {
  color: var(--bar-alert);
}

.summary-line.net {
  font-weight: bold;
  color: var(--color-accent-yellow);
}
</style>

