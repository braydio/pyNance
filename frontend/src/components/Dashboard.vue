<template>
  <div class="dashboard-page">
    <header>
      <div>
        <h1>Brayden.com</h1>
        <h3>Finance</h3>
      </div>
      <nav class="menu">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/teller-dot">Teller.IO</router-link>
        <router-link to="/accounts">Accounts</router-link>
        <router-link to="/transactions">Transactions</router-link>
        <router-link to="/settings">Settings</router-link>
      </nav>
    </header>
    <main>
      <div class="visualization">
        <div class="chart">
          <h2>Net Income vs Spending</h2>
          <button @click="expandDailyCashFlowChart">Expand Chart</button>
          <canvas id="cashFlowChart"></canvas>
        </div>
        <div class="chart">
          <h2>Spending by Category</h2>
          <button @click="toggleCategoryChart">{{ isCategoryPie ? 'Show Bar Chart' : 'Show Pie Chart' }}</button>
          <canvas id="categoryChart"></canvas>
        </div>
        <div class="chart">
          <h2>Net Assets</h2>
          <canvas id="netAssetsChart"></canvas>
        </div>
      </div>
      <div id="expandedChartContainer" v-if="expandedChart">
        <button @click="closeExpandedChart">Close</button>
        <canvas id="expandedDailyCashFlowChart"></canvas>
      </div>
    </main>
    <footer>&copy; Brayden.com</footer>
  </div>
</template>

<script>
import axios from "axios";
import { Chart } from "chart.js/auto";

export default {
  name: "Dashboard",
  data() {
    return {
      cashFlowChart: null,
      categoryChart: null,
      netAssetsChart: null,
      expandedChart: false,
      isCategoryPie: true,
    };
  },
  methods: {
    async fetchAndRenderChart(endpoint, chartInstance, chartId, prepareData) {
      try {
        const response = await axios.get(endpoint);
        if (response.data.status !== "success") {
          console.error(`Failed to fetch data from ${endpoint}`);
          return;
        }
        const ctx = document.getElementById(chartId).getContext("2d");
        if (chartInstance) chartInstance.destroy();
        chartInstance = new Chart(ctx, prepareData(response.data.data));
      } catch (error) {
        console.error(`Error fetching data from ${endpoint}:`, error);
      }
    },
    renderCashFlowChart() {
      this.fetchAndRenderChart(
        "/api/charts/cash_flow",
        this.cashFlowChart,
        "cashFlowChart",
        (data) => ({
          type: "bar",
          data: {
            labels: data.map((entry) => entry.date),
            datasets: [
              { label: "Income", data: data.map((entry) => entry.income), backgroundColor: "#4BC0C0" },
              { label: "Expenses", data: data.map((entry) => entry.expenses), backgroundColor: "#FF6384" },
            ],
          },
          options: {
            responsive: true,
            scales: {
              x: { stacked: true },
              y: { stacked: true, beginAtZero: true },
            },
          },
        })
      );
    },
    renderCategoryChart() {
      this.fetchAndRenderChart(
        "/api/charts/category_breakdown",
        this.categoryChart,
        "categoryChart",
        (data) => ({
          type: this.isCategoryPie ? "pie" : "bar",
          data: {
            labels: data.map((entry) => entry.category),
            datasets: [
              { label: "Spending by Category", data: data.map((entry) => entry.amount), backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56"] },
            ],
          },
          options: {
            responsive: true,
          },
        })
      );
    },
    renderNetAssetsChart() {
      this.fetchAndRenderChart(
        "/api/charts/net_assets",
        this.netAssetsChart,
        "netAssetsChart",
        (data) => ({
          type: "line",
          data: {
            labels: data.map((entry) => entry.date),
            datasets: [
              { label: "Net Worth", data: data.map((entry) => entry.netWorth), borderColor: "#4BC0C0", tension: 0.1, fill: false },
            ],
          },
          options: {
            responsive: true,
          },
        })
      );
    },
    toggleCategoryChart() {
      this.isCategoryPie = !this.isCategoryPie;
      this.renderCategoryChart();
    },
    expandDailyCashFlowChart() {
      this.expandedChart = true;
      this.renderCashFlowChart();
    },
    closeExpandedChart() {
      this.expandedChart = false;
    },
  },
  mounted() {
    this.renderCashFlowChart();
    this.renderCategoryChart();
    this.renderNetAssetsChart();
  },
};
</script>

<style scoped>
.visualization {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}
.chart {
  flex: 1 1 300px;
  padding: 10px;
  border: 1px solid #ccc;
  background: #fff;
}
</style>
