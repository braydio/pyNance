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
        <span>Total Spending: {{ totalSpending.toLocaleString() }}</span>
      </div>
    </div>
    <div class="canvas-wrapper card p-2">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { Chart } from "chart.js/auto";
import axios from "axios";

const chartCanvas = ref(null);
const chartInstance = ref(null);
const chartData = ref({ labels: [], amounts: [], raw: [] });
const daysBack = ref(30);

const totalSpending = computed(() => {
  return chartData.value.amounts.reduce((sum, val) => sum + val, 0);
});

function setRange(range) {
  daysBack.value = range;
  fetchData();
}

async function fetchData() {
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
      updateChart();
    }
  } catch (err) {
    console.error("Error fetching category breakdown data:", err);
  }
}

function updateChart() {
  const canvasEl = chartCanvas.value;
  if (!canvasEl) return;
  const ctx = canvasEl.getContext("2d");
  if (!ctx) return;
  if (chartInstance.value) chartInstance.value.destroy();

  const filtered = chartData.value.raw;
  filtered.sort((a, b) => b.amount - a.amount);
  const top10 = filtered.slice(0, 10);

  chartData.value.labels = top10.map((entry) => entry.category || "Uncategorized");
  chartData.value.amounts = top10.map((entry) => Math.round(entry.amount));

  chartInstance.value = new Chart(ctx, {
    type: "bar",
    data: {
      labels: chartData.value.labels,
      datasets: [
        {
          label: "Spending",
          data: chartData.value.amounts,
          backgroundColor: "#7dd3fc",
          borderColor: "#0284c7",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `$${context.raw.toLocaleString()}`,
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#64748b",
            font: { size: 12 },
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => `$${value}`,
            color: "#64748b",
            font: { size: 12 },
          },
        },
      },
    },
  });
}

onMounted(fetchData);
</script>

<style scoped>
.category-breakdown-chart {
  padding: 1rem;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.header-row h2 {
  margin: 0;
  color: var(--neon-purple);
}

.range-buttons button {
  background: var(--color-bg-secondary);
  border: 1px solid var(--neon-purple);
  color: var(--neon-purple);
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
}

.range-buttons button.active {
  background: var(--neon-purple);
  color: white;
  font-weight: bold;
}

.chart-summary span {
  font-weight: bold;
  color: var(--color-text-light);
}

.canvas-wrapper {
  height: 300px;
  background: var(--themed-bg);
  border-radius: 1rem;
}
</style>
