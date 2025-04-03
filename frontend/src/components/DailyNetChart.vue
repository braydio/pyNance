
<template>
  <div class="daily-net-chart">
    <h2>Daily Net Income</h2>
    <div class="chart-summary">
      <div class="summary-line income">
        Income: ${{ summary.totalIncome.toLocaleString() }}
      </div>
      <div class="summary-line expenses">
        Expenses: ${{ summary.totalExpenses.toLocaleString() }}
      </div>
      <div class="summary-line net">
        Net: ${{ summary.totalNet.toLocaleString() }}
      </div>
    </div>
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import axios from "axios";
import { ref, onMounted, nextTick, computed } from "vue";
import { Chart } from "chart.js/auto";

export default {
  name: "DailyNetChart",
  setup() {
    const chartInstance = ref(null);
    const chartCanvas = ref(null);
    const chartData = ref([]);

    const fetchData = async () => {
      try {
        const response = await axios.get("/api/charts/daily_net");
        if (response.data.status === "success") {
          chartData.value = response.data.data;
          updateChart();
        }
      } catch (error) {
        console.error("Error fetching daily net data:", error);
      }
    };

    const updateChart = async () => {
      await nextTick();
      const canvasEl = chartCanvas.value;
      if (!canvasEl) return;
      const ctx = canvasEl.getContext("2d");
      if (!ctx) return;
      if (chartInstance.value) chartInstance.value.destroy();

      const labels = chartData.value.map((item) => item.date);
      const netValues = chartData.value.map((item) => item.net);

      const gradients = labels.map((_, index) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, canvasEl.height);
        if (netValues[index] >= 0) {
          gradient.addColorStop(0, "#a6e3a1"); // nebula green
          gradient.addColorStop(1, "#5db073");
        } else {
          gradient.addColorStop(0, "#eb6f92"); // nebula rose
          gradient.addColorStop(1, "#a43e5c");
        }
        return gradient;
      });

      const getStyle = (name) =>
        getComputedStyle(document.documentElement)
          .getPropertyValue(name)
          .trim();

      chartInstance.value = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              label: "Net Income",
              data: netValues,
              backgroundColor: gradients,
              borderWidth: 1,
              borderRadius: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: { padding: { top: 20, bottom: 20 } },
          scales: {
            x: {
              ticks: {
                autoSkip: true,
                maxTicksLimit: 10,
                color: getStyle("--color-text-muted"),
                font: { family: "'Fira Code', monospace", size: 10 },
              },
              grid: { color: getStyle("--divider") },
            },
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => `$${value}`,
                color: getStyle("--color-text-muted"),
                font: { family: "'Fira Code', monospace", size: 10 },
              },
              grid: { color: getStyle("--divider") },
            },
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => {
                  const index = context.dataIndex;
                  const dataPoint = chartData.value[index];
                  return [
                    `Net: $${dataPoint.net.toLocaleString()}`,
                    `Income: $${dataPoint.income.toLocaleString()}`,
                    `Expenses: $${dataPoint.expenses.toLocaleString()}`,
                    `Transactions: ${dataPoint.transaction_count}`,
                  ];
                },
              },
              backgroundColor: getStyle("--themed-bg"),
              titleColor: getStyle("--color-accent-yellow"),
              bodyColor: getStyle("--color-text-light"),
              borderColor: getStyle("--color-accent-yellow"),
              borderWidth: 1,
            },
            legend: { display: false },
          },
        },
      });
    };

    const summary = computed(() => {
      const totalIncome = chartData.value.reduce((sum, d) => sum + d.income, 0);
      const totalExpenses = chartData.value.reduce((sum, d) => sum + d.expenses, 0);
      const totalNet = chartData.value.reduce((sum, d) => sum + d.net, 0);
      return { totalIncome, totalExpenses, totalNet };
    });

    onMounted(() => {
      fetchData();
    });

    return {
      chartCanvas,
      fetchData,
      summary,
    };
  },
};
</script>

<style scoped>
@import "@/styles/global-colors.css";

.daily-net-chart {
  margin: 1rem;
  background-color: var(--themed-bg);
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow), 0 0 6px var(--hover-glow);
  position: relative;
  opacity: 0.95;
  height: 400px;
  border: 1px solid var(--divider);
  transition: box-shadow 0.3s ease, background-color 0.3s ease;
}

.chart-summary {
  position: absolute;
  top: 10px;
  right: 10px;
  background: var(--color-bg-secondary);
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-family: "SourceCodeVF", monospace;
  color: var(--color-text-muted);
  z-index: 10;
  text-align: right;
  box-shadow: 0 2px 8px var(--shadow);
  backdrop-filter: blur(4px);
  border: 1px solid var(--divider);
  transition: background 0.3s ease;
}

.chart-summary .summary-line {
  margin: 2px 0;
  line-height: 1.2;
  color: var(--color-text-muted);
}

.chart-summary .summary-line.net {
  font-weight: bold;
  font-size: 1.3em;
  color: var(--color-accent-mint);
  text-shadow: 0 0 4px var(--neon-mint);
}
</style>

