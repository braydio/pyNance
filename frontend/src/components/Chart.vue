<template>
  <div class="chart-container">
    <h2>{{ title }}</h2>
    <button v-if="toggleText" @click="toggleView">{{ toggleText }}</button>
    <canvas :id="chartId"></canvas>
  </div>
</template>

<script>
import { Chart } from "chart.js/auto";

export default {
  props: {
    title: String,
    chartId: String,
    chartData: Object, // Data for the chart
    chartType: {
      type: String,
      default: "bar", // Default chart type
    },
    toggleText: String,
  },
  data() {
    return {
      chartInstance: null,
    };
  },
  methods: {
    toggleView() {
      this.$emit("toggle");
    },
    renderChart() {
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }

      const ctx = document.getElementById(this.chartId).getContext("2d");
      this.chartInstance = new Chart(ctx, {
        type: this.chartType,
        data: this.chartData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
        },
      });
    },
  },
  watch: {
    chartData: "renderChart", // Re-render chart when data changes
  },
  mounted() {
    this.renderChart();
  },
};
</script>

<style scoped>
.chart-container {
  margin: 20px 0;
}
</style>
