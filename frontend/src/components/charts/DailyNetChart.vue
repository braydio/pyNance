
<template>
  <div class="daily-net-chart">
    <div class="header-row">
      <h2>Daily Net Income</h2>
      <button class="zoom-toggle" @click="toggleZoom">
        {{ zoomedOut ? 'Zoom In' : 'Zoom Out' }}
      </button>
    </div>
    <div class="chart-summary">
      <div class="summary-line income">
        Income: ${{ summary.totalIncome.toLocaleString() }}
      </div>
      <div class="summary-line expenses">
        Expenses: ${{ summary.totalExpenses.toLocaleString() }}
      </div>
      <div class="summary-line net">
       Net Total: ${{ summary.totalNet.toLocaleString() }}
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
  setup(_, { emit }) {
    const chartInstance = ref(null);
    const chartCanvas = ref(null);
    const chartData = ref([]);
    const zoomedOut = ref(false);

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

    const toggleZoom = () => {
      zoomedOut.value = !zoomedOut.value;
      updateChart();
    };

    const updateChart = async () => {
      await nextTick();
      const canvasEl = chartCanvas.value;
      if (!canvasEl) return;
      const ctx = canvasEl.getContext("2d");
      if (!ctx) return;
      if (chartInstance.value) chartInstance.value.destroy();

      const now = new Date();
      const rangeStart = new Date();
      if (!zoomedOut.value) {
        rangeStart.setMonth(rangeStart.getMonth() - 1);
      } else {
        rangeStart.setMonth(rangeStart.getMonth() - 6);
      }

      const filtered = chartData.value.filter(item => {
        const d = new Date(item.date);
        return d >= rangeStart && d <= now;
      });

      const labels = filtered.map((item) => item.date);
      const netValues = filtered.map((item) => item.net);
      const incomeValues = filtered.map((item) => item.income);
      const expenseValues = filtered.map((item) => item.expenses);

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
              type: "bar",
              label: "Income",
              data: incomeValues,
              backgroundColor: "#5db073",
              borderRadius: 4,
              barThickness: 20,
            },
            {
              type: "bar",
              label: "Expenses",
              data: expenseValues,
              backgroundColor: "#a43e5c",
              borderRadius: 4,
              barThickness: 20,
            },
            {
              type: "line",
              label: "Net",
              data: netValues,
              borderColor: getStyle("--color-accent-mint"),
              backgroundColor: getStyle("--color-accent-mint"),
              tension: 0.3,
              borderWidth: 2,
              pointRadius: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: { padding: { top: 20, bottom: 20 } },
          scales: {
            x: {
              stacked: true,
              ticks: {
                maxTicksLimit: 14,
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
                  const dataPoint = filtered[index];
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
            legend: { display: true },
          },
          onClick: (evt) => {
            const points = chartInstance.value.getElementsAtEventForMode(
              evt,
              "nearest",
              { intersect: true },
              false
            );
            if (points.length) {
              const index = points[0].index;
              const date = filtered[index].date;
              emit("bar-click", date);
            }
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
      toggleZoom,
      zoomedOut,
    };
  },
};
</script>



<style scoped>
.daily-net-chart {
  margin: 1rem;
  background-color: var(--color-bg-sec);
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow), 0 0 6px var(--hover-glow);
  position: relative;
  opacity: 0.95;
  height: 400px;
  min-width: 700px;
  width: 100%;
  border: 1px solid var(--divider);
  transition: box-shadow 0.3s ease, background-color 0.3s ease;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.zoom-toggle {
  background: var(--color-accent-yellow);
  border: none;
  color: var(--color-text-dark);
  padding: 0.25rem 0.75rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
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
  border: 5px solid var(--divider);
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

