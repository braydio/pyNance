
<template>
  <div class="chart-container card">
    <div class="flex-between mb-2">
      <h2 class="heading-md">{{ chartTypeLabel }} </h2>
      <div>
        <button
          v-for="type in chartTypes"
          :key="type.value"
          class="btn btn-pill m-1"
          :class="{'btn-success': activeChart === type.value, 'btn-outline': activeChart !== type.value}"
          @click="setChartType(type.value)"
        >
          {{ type.label }}
        </button>
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
  name: "NetYearComparisonChart",
  setup() {
    const chartCanvas = ref(null);
    const chartInstance = ref(null);
    const chartData = ref([]);
    const activeChart = ref('assets');

    const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

    const thisYear = new Date().getFullYear();
    const lastYear = thisYear - 1;

    const chartTypes = [
      { label: "Assets", value: "assets" },
      { label: "Liabilities", value: "liabilities" },
      { label: "Net", value: "netWorth" }
    ];

    const chartTypeLabel = ref('Assets');

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

    const getMonthIndex = (dateString) => parseInt(dateString.split("-")[1], 10) - 1;

    const createMonthlyData = (year, dataKey) => {
      const monthlyData = new Array(12).fill(null);

      chartData.value.forEach(item => {
        if (parseInt(item.date.split("-")[0], 10) === year) {
          monthlyData[getMonthIndex(item.date)] = item[dataKey];
        }
      });
      return monthlyData;
    };

    const buildChart = () => {
      if (chartInstance.value) chartInstance.value.destroy();

      const ctx = chartCanvas.value.getContext("2d");

      chartInstance.value = new Chart(ctx, {
        type: "line",
        data: {
          labels: MONTH_LABELS,
          datasets: [
            {
              label: `${chartTypeLabel.value} (${lastYear})`,
              data: createMonthlyData(lastYear, activeChart.value),
              borderColor: getComputedStyle(document.documentElement).getPropertyValue('--bar-neutral').trim(),
              backgroundColor: "transparent",
              tension: 0.1,
              borderDash: [5, 5],
            },
            {
              label: `${chartTypeLabel.value} (${thisYear})`,
              data: createMonthlyData(thisYear, activeChart.value),
              borderColor: getComputedStyle(document.documentElement).getPropertyValue('--bar-success').trim(),
              backgroundColor: "transparent",
              tension: 0.1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: { legend: { labels: { color: getComputedStyle(document.documentElement).getPropertyValue('--color-text-light').trim() } } },
          scales: {
            x: { ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--color-text-muted').trim() }, grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--divider').trim() } },
            y: { ticks: { display: false }, grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--divider').trim() } },
          },
        },
      });
    };

    const setChartType = (type) => {
      activeChart.value = type;
      chartTypeLabel.value = chartTypes.find(t => t.value === type).label;
      buildChart();
    };

    return { chartCanvas, chartTypes, activeChart, setChartType, chartTypeLabel };
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
</style>

