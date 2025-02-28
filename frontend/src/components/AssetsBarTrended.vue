<template>
    <div class="chart-container">
      <div class="chart-title-row">
        <h2>Net Assets vs. Liabilities</h2>
        <!-- Current Totals Summary -->
        <div class="chart-summary" v-if="metadata">
          <h4>Current Totals</h4>
          <div class="summary-line assets">
            Assets: {{ formatCurrency(metadata.total_assets) }}
          </div>
          <div class="summary-line liabilities">
            Liabilities: {{ formatCurrency(metadata.total_liabilities, true) }}
          </div>
          <div class="summary-line net">
            Net: {{ formatCurrency(metadata.net_now) }}
          </div>
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
  
      // The array of historical data: { date, assets, liabilities, net }
      const chartData = ref([]);
      // The metadata object: { total_assets, total_liabilities, net_now }
      const metadata = ref(null);
  
      // Function to fetch data from /net_assets
      const fetchData = async () => {
        try {
          const response = await axios.get("/api/charts/net_assets");
          if (response.data.status === "success") {
            chartData.value = response.data.data || [];
            metadata.value = response.data.metadata || null;
            updateChart();
          } else {
            console.error("Failed to fetch net_assets:", response.data);
          }
        } catch (error) {
          console.error("Error fetching net assets data:", error);
        }
      };
  
      // Utility to format currency, using parentheses for negative
      const formatCurrency = (val) => {
        const number = parseFloat(val) || 0;
        if (number < 0) {
          return `($${Math.abs(number).toLocaleString()})`;
        }
        return `$${number.toLocaleString()}`;
      };
  
      // Helper: Convert YYYY-MM-DD to MMM
      const formatMMM = (dateString) => {
        const [yyyy, mm, dd] = dateString.split("-");
        const dateObj = new Date(`${yyyy}-${mm}-${dd}T00:00:00`);
        // Basic list of month abbreviations
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        return monthNames[dateObj.getMonth()];
      };
  
      const updateChart = async () => {
        await nextTick();
        const canvasEl = chartCanvas.value;
        if (!canvasEl) return;
  
        const ctx = canvasEl.getContext("2d");
        if (!ctx) return;
  
        if (chartInstance.value) {
          chartInstance.value.destroy();
        }
  
        // Prepare data
        const labels = chartData.value.map(item => item.date);
        const assetsData = chartData.value.map(item => item.assets);
        const liabilitiesData = chartData.value.map(item => item.liabilities);
        const netData = chartData.value.map(item => item.net);
  
        // We'll do all lines
        chartInstance.value = new Chart(ctx, {
          type: "line",
          data: {
            labels,
            datasets: [
              {
                label: "Assets",
                data: assetsData,
                borderColor: "#83a598",   // Gruvbox aqua
                backgroundColor: "rgba(131, 165, 152, 0.2)",
                fill: false,
                tension: 0.1,
              },
              {
                label: "Liabilities",
                data: liabilitiesData,
                borderColor: "#fb4934",   // Gruvbox red
                backgroundColor: "rgba(251, 73, 52, 0.2)",
                fill: false,
                tension: 0.1,
              },
              {
                label: "Net",
                data: netData,
                borderColor: "#fabd2f",   // Gruvbox yellow
                backgroundColor: "rgba(250, 189, 47, 0.2)",
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
                // We'll do a custom callback to display MMM
                ticks: {
                  color: "#ebdbb2",
                  callback: function (value, index) {
                    // 'this.getLabelForValue(value)' => date string
                    const dateString = this.getLabelForValue(value);
                    return formatMMM(dateString);
                  },
                },
                grid: {
                  color: "#504945",
                },
              },
              y: {
                beginAtZero: true,
                ticks: {
                  color: "#ebdbb2",
                  callback: (val) => {
                    const number = parseFloat(val);
                    if (number < 0) {
                      return `($${Math.abs(number).toLocaleString()})`;
                    }
                    return `$${number.toLocaleString()}`;
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
                  label: (context) => {
                    const label = context.dataset.label;
                    const val = context.raw;
                    if (val < 0) {
                      return `${label}: ($${Math.abs(val).toLocaleString()})`;
                    }
                    return `${label}: $${val.toLocaleString()}`;
                  },
                  title: (context) => {
                    // Use MMM for the title as well
                    const idx = context[0].dataIndex;
                    const dateString = labels[idx];
                    return formatMMM(dateString);
                  },
                },
                backgroundColor: "#3c3836",
                titleColor: "#fabd2f",
                bodyColor: "#ebdbb2",
                borderColor: "#fabd2f",
                borderWidth: 1,
              },
              legend: {
                labels: {
                  color: "#ebdbb2",
                },
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
        metadata,
        formatCurrency,
      };
    },
  };
  </script>
  
  <style scoped>
  .chart-container {
    margin: 1rem;
    background-color: #282828;
    padding: 1rem;
    border-radius: 8px;
    opacity: 0.95;
    position: relative;
    max-height: 85%; /* Adjust as needed */
  }
  
  /* Title + summary row at the top */
  .chart-title-row {
    display:inline-block;
    align-items: right;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }
  
  .chart-summary {
    background: rgba(44, 44, 44, 0.8);
    padding: 0.5rem;
    border-radius: 4px;
    font-family: "Fira Code", monospace;
    color: #ebdbb2;
    text-align: right;
  }
  
  .chart-summary h4 {
    margin: 0 0 0.5rem 0;
    color: #fabd2f;
  }
  
  .summary-line {
    margin: 4px 0;
  }
  
  .summary-line.assets {
    color: #83a598; /* aqua */
  }
  .summary-line.liabilities {
    color: #fb4934; /* red */
  }
  .summary-line.net {
    color: #fabd2f; /* yellow */
    font-weight: bold;
  }
  
  </style>
  