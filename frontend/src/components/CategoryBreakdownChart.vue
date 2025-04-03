
<template>
  <div class="category-breakdown-chart">
    <div class="header-row">
      <h2>Spending by Category</h2>
      <div class="chart-summary">
        <span>Total Spending: ${{ totalSpending.toLocaleString() }}</span>
      </div>
    </div>
    <div class="canvas-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { ref, onMounted, nextTick, computed } from "vue";
import { Chart } from "chart.js/auto";

export default {
  name: "CategoryBreakdownChart",
  setup() {
    const chartCanvas = ref(null);
    const chartInstance = ref(null);
    const chartData = ref({ labels: [], amounts: [] });

    const getStyle = (name) =>
      getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();

    const totalSpending = computed(() => {
      return chartData.value.amounts.reduce((sum, val) => sum + val, 0);
    });

    const fetchData = async () => {
      try {
        const response = await axios.get("/api/charts/category_breakdown");
        if (response.data.status === "success") {
          let data = response.data.data;
          data.sort((a, b) => b.amount - a.amount);
          const top10 = data.slice(0, 10);
          chartData.value.labels = top10.map(entry => entry.category || "Uncategorized");
          chartData.value.amounts = top10.map(entry => Math.round(entry.amount));
          updateChart();
        }
      } catch (err) {
        console.error("Error fetching category breakdown data:", err);
      }
    };

    const updateChart = async () => {
      await nextTick();
      const canvasEl = chartCanvas.value;
      if (!canvasEl) return;
      const ctx = canvasEl.getContext("2d");
      if (!ctx) return;
      if (chartInstance.value) chartInstance.value.destroy();

      const gradients = chartData.value.amounts.map(() => {
        const gradient = ctx.createLinearGradient(0, 0, 0, canvasEl.height);
        gradient.addColorStop(0, getStyle("--bar-gradient-start"));
        gradient.addColorStop(1, getStyle("--bar-gradient-end"));
        return gradient;
      });

      chartInstance.value = new Chart(ctx, {
        type: "bar",
        data: {
          labels: chartData.value.labels,
          datasets: [
            {
              label: "Spending",
              data: chartData.value.amounts,
              backgroundColor: gradients,
              borderWidth: 1,
              borderRadius: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: {
            padding: { top: 20, bottom: 20 },
          },
          scales: {
            x: {
              ticks: {
                color: getStyle("--color-text-muted"),
                font: { family: "'SourceCodeVF', monospace", size: 10 },
                autoSkip: true,
                maxTicksLimit: 10,
              },
              grid: {
                color: getStyle("--divider"),
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => `$${value}`,
                color: getStyle("--color-text-muted"),
                font: { family: "'SourceCodeVF', monospace", size: 10 },
              },
              grid: {
                color: getStyle("--divider"),
              },
            },
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) =>
                  `${context.label}: $${context.raw.toLocaleString()}`,
              },
              backgroundColor: getStyle("--themed-bg"),
              titleColor: getStyle("--color-accent-yellow"),
              bodyColor: getStyle("--color-text-light"),
              borderColor: getStyle("--color-accent-yellow"),
              borderWidth: 1,
            },
            legend: {
              display: false,
            },
          },
        },
      });
    };

    onMounted(() => {
      fetchData();
    });

    return {
      chartCanvas,
      fetchData,
      totalSpending,
    };
  },
};
</script>

<style scoped>
@import '@/styles/global-colors.css';

.category-breakdown-chart {
  margin: 1rem;
  background-color: var(--themed-bg);
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow), 0 0 6px var(--hover-glow);
  opacity: 0.95;
  position: relative;
  border: 1px solid var(--divider);
  transition: background 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.header-row h2 {
  margin: 0;
  font-size: 1.2rem;
  color: var(--color-text-light);
}

.chart-summary {
  background: var(--color-bg-secondary);
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-family: "SourceCodeVF", monospace;
  color: var(--color-text-light);
  box-shadow: 0 2px 8px var(--shadow);
  border: 1px solid var(--divider);
  backdrop-filter: blur(4px);
}

.canvas-wrapper {
  flex-grow: 1;
  min-height: 240px;
  position: relative;
}
</style>

