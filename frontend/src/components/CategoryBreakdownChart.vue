
<template>
  <div class="category-breakdown-chart">
    <div class="header-row">
      <h2>Spending by Category</h2>
      <div class="range-buttons">
        <button @click="setRange(7)" :class="{ active: daysBack === 7 }">7d</button>
        <button @click="setRange(30)" :class="{ active: daysBack === 30 }">30d</button>
        <button @click="setRange(90)" :class="{ active: daysBack === 90 }">90d</button>
      </div>
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
    const chartData = ref({ labels: [], amounts: [], raw: [] });
    const daysBack = ref(30);

    const getStyle = (name) =>
      getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();

    const totalSpending = computed(() => {
      return chartData.value.amounts.reduce((sum, val) => sum + val, 0);
    });

    const setRange = (range) => {
      daysBack.value = range;
      fetchData();
    };

    const fetchData = async () => {
      try {
        const end = new Date();
        const start = new Date();
        start.setDate(end.getDate() - daysBack.value);
        const startStr = start.toISOString().slice(0, 10);
        const endStr = end.toISOString().slice(0, 10);

        const response = await axios.get("/api/charts/category_breakdown", {
          params: { start_date: startStr, end_date: endStr },
        });

        if (response.data.status === "success") {
          chartData.value.raw = response.data.data;
          await updateChart();
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

      const filtered = chartData.value.raw;
      filtered.sort((a, b) => b.amount - a.amount);
      const top10 = filtered.slice(0, 10);

      chartData.value.labels = top10.map(entry => entry.category || "Uncategorized");
      chartData.value.amounts = top10.map(entry => Math.round(entry.amount));

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
      daysBack,
      setRange,
    };
  },
};
</script>


