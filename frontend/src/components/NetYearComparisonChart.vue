<template>
    <div class="chart-container">
      <h2>Assets: Last Year vs. This Year</h2>
      <canvas ref="chartCanvas"></canvas>
    </div>
  </template>
  
  <script>
  import axios from "axios";
  import { ref, onMounted, nextTick } from "vue";
  import { Chart } from "chart.js/auto";
  
  const GREEN_CURRENT = "#8ec07c";      
  const GREEN_LAST_YEAR = "rgba(142, 192, 124, 0.4)";
  
  export default {
    name: "AssetsYearComparisonChart",
    setup() {
      const chartCanvas = ref(null);
      const chartInstance = ref(null);
      const chartData = ref([]);
      const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun",
                            "Jul","Aug","Sep","Oct","Nov","Dec"];
  
      const thisYear = new Date().getFullYear();
      const lastYear = thisYear - 1;
  
      onMounted(() => {
        fetchData();
      });
  
      const fetchData = async () => {
        try {
          const response = await axios.get("/api/charts/net_assets");
          if (response.data.status === "success") {
            chartData.value = response.data.data || [];
            await nextTick();
            buildChart();
          }
        } catch (error) {
          console.error(error);
        }
      };
  
      const getMonthIndex = (dateString) => {
        const [yyyy, mm] = dateString.split("-");
        return parseInt(mm, 10) - 1;
      };
  
      const createMonthlyData = (year, dataKey) => {
        const monthlyData = new Array(12).fill(null);
        const monthlyObjects = new Array(12).fill(null);
  
        chartData.value.forEach(item => {
          const [yyyyStr] = item.date.split("-");
          if (parseInt(yyyyStr, 10) === year) {
            const monthIdx = getMonthIndex(item.date);
            monthlyData[monthIdx] = item[dataKey];
            monthlyObjects[monthIdx] = item; // store for tooltips
          }
        });
        return { monthlyData, monthlyObjects };
      };
  
      const buildChart = () => {
        if (chartInstance.value) {
          chartInstance.value.destroy();
        }
        const ctx = chartCanvas.value.getContext("2d");
  
        const { monthlyData: lastYearData, monthlyObjects: lastYearObjs } =
          createMonthlyData(lastYear, "assets");
        const { monthlyData: thisYearData, monthlyObjects: thisYearObjs } =
          createMonthlyData(thisYear, "assets");
  
        chartInstance.value = new Chart(ctx, {
          type: "line",
          data: {
            labels: MONTH_LABELS,
            datasets: [
              {
                label: `Assets (${lastYear})`,
                data: lastYearData,
                borderColor: GREEN_LAST_YEAR,
                backgroundColor: "transparent",
                tension: 0.1,
                borderDash: [5, 5],
              },
              {
                label: `Assets (${thisYear})`,
                data: thisYearData,
                borderColor: GREEN_CURRENT,
                backgroundColor: "transparent",
                tension: 0.1,
                borderDash: [],
              },
            ],
          },
          options: {
            responsive: true,
            scales: {
              x: { ticks: { color: "#ebdbb2" }, grid: { color: "#504945" } },
              y: { ticks: { display: false }, grid: { color: "#504945" } },
            },
            plugins: {
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const idx = context.dataIndex;
                    const dsIdx = context.datasetIndex;
                    if (dsIdx === 0) {
                      // Last year
                      const val = lastYearObjs[idx]?.assets ?? null;
                      return val !== null 
                        ? `Last Year Assets: $${val.toLocaleString()}`
                        : "No data";
                    } else {
                      // This year
                      const val = thisYearObjs[idx]?.assets ?? null;
                      return val !== null 
                        ? `This Year Assets: $${val.toLocaleString()}`
                        : "No data";
                    }
                  },
                  title: (ctx) => ctx[0].label,
                },
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
  
      return { chartCanvas };
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
    max-height: 400px; /* Adjust as needed */
    width: auto;   /* Adjust as needed */
  }
  </style>
  