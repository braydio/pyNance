<template>
  <div class="net-chart">
    <h2>{{ chartTitle }}</h2>
    <div class="chart-summary">
      <div class="summary-line income">
        Income: ${{ formatAmount(summary.totalIncome) }}
      </div>
      <div class="summary-line expenses">
        Expenses: ${{ formatAmount(summary.totalExpenses) }}
      </div>
      <div class="summary-line net">
        Net: ${{ formatAmount(summary.totalNet) }}
      </div>
    </div>

    <div class="chart-controls">
      <button @click="changeGranularity('daily')" :class="{ active: granularity === 'daily' }">Daily</button>
      <button @click="setWeekly" :class="{ active: granularity === 'weekly' }">Weekly</button>
      <button @click="setMonthly" :class="{ active: granularity === 'monthly' }">Monthly</button>
    </div>

    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import api from '@/services/api.js'
import { ref, onMounted, nextTick, computed } from "vue";
import { Chart } from "chart.jsauto";
import { formatAmount } from "@/utils/format"

export default {
  name: "NetIncomeChart",
  setup() {
    const chartInstance = ref(null);
    const chartCanvas = ref(null);
    const chartData = ref([]);
    const granularity = ref("daily");

    const fetchData = async () => {
      try {
        const response = await api.fetchCashFlow({
          granularity: granularity.value,
        });
        if (response.status === "success") {
          chartData.value = response.data;
          updateChart();
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    const updateChart = async () => {
      await nextTick();
      const ctx = chartCanvas.value.getContext("2d");
      if (chartInstance.value) {
        chartInstance.value.destroy();
      }

      const netValues = chartData.value.map(item => item.income - item.expenses);
      const gradients = netValues.map(value => {
        const gradient = ctx.createLinearGradient(0, 0, 0, chartCanvas.value.height);
        if (value >= 0) {
          gradient.addColorStop(0, "#b8bb26");
          gradient.addColorStop(1, "#98971a");
        } else {
          gradient.addColorStop(0, "#fb4934");
          gradient.addColorStop(1, "#cc241d");
        }
        return gradient;
      });

      if (chartInstance.value) chartInstance.value.destroy();
      chartInstance.value = new Chart(ctx, {
        type: "bar",
        data: {
          labels: chartData.value.map(item => item.date),
          datasets: [{
            label: "Net Income",
            data: netValues,
            backgroundColor: gradients,
            borderWidth: 1,
            borderRadius: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: { padding: { top: 20, bottom: 20 } },
          scales: {
            x: { ticks: { color: "#ebdbb2" }, grid: { color: "#504945" } },
            y: { beginAtZero: true, ticks: { callback: (value) => `$${value}`, color: "#ebdbb2" } },
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: context => {
                  const index = context.dataIndex;
                  const dataPoint = chartData.value[index];
                  return [
                    `Net: ${formatAmount(dataPoint.income - dataPoint.expenses)}`,
                    `Income: ${formatAmount(dataPoint.income)}`,
                    `Expenses: ${formatAmount(dataPoint.expenses)}`
                  ];
                }
              },
              backgroundColor: "#3c3836",
              titleColor: "#fabd2f",
              bodyColor: "#ebdbb2",
              borderColor: "#fabd2f",
              borderWidth: 1,
            },
            legend: { display: false }
          }
        }
      });
    };

    const summary = computed(() => {
      const totalIncome = chartData.value.reduce((sum, d) => sum + d.income, 0);
      const totalExpenses = chartData.value.reduce((sum, d) => sum + d.expenses, 0);
      const totalNet = totalIncome - totalExpenses;
      return { totalIncome, totalExpenses, totalNet };
    });

    const setWeekly = () => {
      granularity.value = "weekly";
      fetchData();
    };

    const setMonthly = () => {
      granularity.value = "monthly";
      fetchData();
    };

    onMounted(() => fetchData());

    return {
      chartCanvas,
      summary,
      granularity,
      setWeekly,
      setMonthly,
    };
  }
};
</script>
