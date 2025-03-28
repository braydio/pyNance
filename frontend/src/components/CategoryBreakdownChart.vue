<template>
  <div class="category-breakdown-chart">
    <h2>Spending by Category</h2>
    <div class="chart-summary">
      <span>Total Spending: ${{ totalSpending.toLocaleString() }}</span>
    </div>
    <canvas ref="chartCanvas"></canvas>
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
    // chartData: { labels: string[], amounts: number[] }
    const chartData = ref({ labels: [], amounts: [] });

    const totalSpending = computed(() => {
      return chartData.value.amounts.reduce((sum, val) => sum + val, 0);
    });

    const fetchData = async () => {
      try {
        const response = await axios.get("/api/charts/category_breakdown");
        if (response.data.status === "success") {
          // Expect data as an array of objects: { category, amount }
          let data = response.data.data;
          // Sort descending and take top 10
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
      if (!canvasEl) {
        console.error("Canvas element not available.");
        return;
      }
      const ctx = canvasEl.getContext("2d");
      if (!ctx) {
        console.error("Canvas 2D context not available.");
        return;
      }
      if (chartInstance.value) {
        chartInstance.value.destroy();
      }

      // Create custom gradients for each bar.
      const gradients = chartData.value.amounts.map((amount, index) => {
        const gradient = ctx.createLinearGradient(0, 0, 0, canvasEl.height);
        // For spending, we use a Gruvbox-inspired blue-green palette.
        gradient.addColorStop(0, "#83a598"); // light tone
        gradient.addColorStop(1, "#458588"); // darker tone
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
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: {
            padding: {
              top: 20,
              bottom: 20,
            },
          },
          scales: {
            x: {
              ticks: {
                color: "#ebdbb2",
                font: {
                  family: "'Fira Code', monospace",
                  size: 10,
                },
                autoSkip: true,
                maxTicksLimit: 10,
              },
              grid: {
                color: "#504945",
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => `$${value}`,
                color: "#ebdbb2",
                font: {
                  family: "'Fira Code', monospace",
                  size: 10,
                },
              },
              grid: {
                color: "#504945",
              },
            },
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) =>
                  `${context.label}: $${context.raw.toLocaleString()}`,
              },
              backgroundColor: "#3c3836",
              titleColor: "#fabd2f",
              bodyColor: "#ebdbb2",
              borderColor: "#fabd2f",
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

<!-- Scoped styles for this component -->
<style scoped>
@import '@/styles/global-colors.css';

.category-breakdown-chart {
  margin: 1rem;
  background-color: #282828;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  opacity: 0.95;
  position: relative;
  height: 300px;
}
.chart-summary {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(44, 44, 44, 0.8);
  padding: 0.5rem;
  border-radius: 4px;
  font-family: "Fira Code", monospace;
  color: #fabd2f;
  z-index: 10;
}

</style>
