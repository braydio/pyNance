<template>
    <div class="daily-net-chart">
      <h2>Daily Net Income (30 Day Rolling)</h2>
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
      // chartData: array of objects, each containing: date, net, income, expenses, transaction_count
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
        if (!canvasEl) {
          console.error("Canvas element is not available.");
          return;
        }
        const ctx = canvasEl.getContext("2d");
        if (!ctx) {
          console.error("Canvas 2D context is not available.");
          return;
        }
        if (chartInstance.value) {
          chartInstance.value.destroy();
        }
  
        // Prepare labels and net values.
        const labels = chartData.value.map(item => item.date);
        const netValues = chartData.value.map(item => item.net);
  
        // Create a gradient for each bar: green gradient for positive, red gradient for negative.
        const gradients = labels.map((_, index) => {
          const gradient = ctx.createLinearGradient(0, 0, 0, canvasEl.height);
          if (netValues[index] >= 0) {
            gradient.addColorStop(0, "#b8bb26"); // light green
            gradient.addColorStop(1, "#98971a"); // dark green
          } else {
            gradient.addColorStop(0, "#fb4934"); // light red
            gradient.addColorStop(1, "#cc241d"); // dark red
          }
          return gradient;
        });
  
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
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
              padding: { top: 20, bottom: 20 }
            },
            scales: {
              x: {
                ticks: {
                  autoSkip: true,
                  maxTicksLimit: 10,
                  color: "#ebdbb2",
                  font: { family: "'Fira Code', monospace", size: 10 }
                },
                grid: { color: "#504945" }
              },
              y: {
                beginAtZero: true,
                ticks: {
                  callback: (value) => `$${value}`,
                  color: "#ebdbb2",
                  font: { family: "'Fira Code', monospace", size: 10 }
                },
                grid: { color: "#504945" }
              }
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
                      `Transactions: ${dataPoint.transaction_count}`
                    ];
                  }
                },
                backgroundColor: "#3c3836",
                titleColor: "#fabd2f",
                bodyColor: "#ebdbb2",
                borderColor: "#fabd2f",
                borderWidth: 1
              },
              legend: { display: false }
            }
          }
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
    }
  };
  </script>
  
  <style scoped>
  .daily-net-chart {
    margin: 1rem;
    background-color: #282828;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
    position: relative;
    opacity: 0.95;
    height: 300px;
  }
  
  /* Net summary overlay positioned at the top right */
  .chart-summary {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(44, 44, 44, 0.8);
    padding: 0.5rem;
    border-radius: 4px;
    font-family: "Fira Code", monospace;
    color: #fabd2f;
    z-index: 10;
    text-align: right;
  }
  
  /* Stack summary lines vertically */
  .chart-summary .summary-line {
    margin: 2px 0;
  }
  
  /* Different styling for the net total */
  .chart-summary .summary-line.net {
    font-weight: bold;
    color: #fb4934;
    font-size: 1.1em;
  }
  </style>
  