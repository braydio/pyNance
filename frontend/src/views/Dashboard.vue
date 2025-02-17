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
      <!-- Visualization Section -->
      <div class="visualization">
        <!-- Monthly Cash Flow Chart -->
        <div class="chart-cashflow">
          <h2>Net Income vs Spending</h2>
          <button @click="expandDailyCashFlowChart">Expand Chart</button>
          <canvas id="cashFlowChart"></canvas>
        </div>
        <!-- Optional Reset Filter Button -->
        <button v-if="showReset" id="resetFilter" @click="resetFilter">
          Reset Filter
        </button>
        <!-- Category Breakdown Chart -->
        <div class="chart-categories">
          <h2>Spending by Category</h2>
          <button @click="toggleCategoryChart">
            Toggle Chart ({{ isCategoryPie ? 'Pie' : 'Bar' }})
          </button>
          <canvas id="categoryBreakdownChart"></canvas>
        </div>
        <!-- Net Assets Chart -->
        <div class="chart-netassets">
          <h2>Net Assets</h2>
          <button @click="toggleNetAssetsChart">
            Toggle ({{ isNetAssetsStacked ? 'Stacked' : 'Net Only' }})
          </button>
          <canvas id="netAssetsChart"></canvas>
        </div>
      </div>

      <!-- Expanded Daily Cash Flow Chart -->
      <div id="expandedCashFlowContainer" v-if="expandedChart">
        <button id="closeExpandedCashFlow" @click="closeExpandedCashFlow">
          Close
        </button>
        <canvas id="dailyCashFlowChart"></canvas>
      </div>

      <!-- Transactions Table -->
      <div class="transactions">
        <h3>Transactions</h3>
        <table id="transactions-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Name</th>
              <th>Category</th>
              <th>Merchant</th>
              <th>Account</th>
              <th>Institution</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="paginatedTransactions.length === 0">
              <td colspan="7">No transactions available</td>
            </tr>
            <tr v-for="tx in paginatedTransactions" :key="tx.transaction_id">
              <td>{{ tx.date }}</td>
              <td>{{ formatAmount(tx.amount) }}</td>
              <td>{{ tx.name }}</td>
              <td>{{ tx.category }}</td>
              <td>{{ tx.merchant_name }}</td>
              <td>{{ tx.account_name }}</td>
              <td>{{ tx.institution_name }}</td>
            </tr>
          </tbody>
        </table>
        <div id="pagination-controls">
          <button @click="changePage(-1)">Previous</button>
          <span>Page {{ currentPage }}</span>
          <button @click="changePage(1)">Next</button>
        </div>
      </div>
    </main>
    <footer>&copy; This is fine. I'm fine.</footer>
  </div>
</template>

<script>
import axios from "axios";
import Chart from "chart.js/auto";

export default {
  name: "Dashboard",
  data() {
    return {
      // Transactions and pagination
      allTransactions: [],
      currentPage: 1,
      pageSize: 50,
      showReset: false,
      // Chart toggles
      isCategoryPie: true,
      isStackedView: true,
      isNetAssetsStacked: true,
      // Chart.js instances
      cashFlowChart: null,
      categoryChart: null,
      netAssetsChart: null,
      dailyCashFlowChart: null,
      // Expanded chart flag
      expandedChart: false
    };
  },
  computed: {
    paginatedTransactions() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.allTransactions.slice(start, start + this.pageSize);
    }
  },
  methods: {
    async fetchTransactions() {
      try {
        const response = await axios.get(
          `/api/transactions/?page=${this.currentPage}&page_size=${this.pageSize}`
        );
        if (response.data.status === "success") {
          this.allTransactions = response.data.data.transactions;
        }
      } catch (err) {
        console.error("Error fetching transactions:", err);
      }
    },
    changePage(delta) {
      this.currentPage += delta;
      if (this.currentPage < 1) this.currentPage = 1;
      this.fetchTransactions();
    },
    resetFilter() {
      this.fetchTransactions();
      this.showReset = false;
    },
    toggleCategoryChart() {
      this.isCategoryPie = !this.isCategoryPie;
      this.renderCategoryChart();
    },
    toggleNetAssetsChart() {
      this.isNetAssetsStacked = !this.isNetAssetsStacked;
      this.renderNetAssetsChart();
    },
    expandDailyCashFlowChart() {
      this.expandedChart = true;
      this.renderDailyCashFlowChart();
    },
    closeExpandedCashFlow() {
      this.expandedChart = false;
    },
    async renderCashFlowChart() {
      try {
        const response = await axios.get("/api/charts/cash_flow");
        if (response.data.status !== "success") return;
        const data = response.data.data;
        const labels = data.map(entry => entry.month);
        const incomeData = data.map(entry => Math.round(entry.income));
        const expenseData = data.map(entry => -Math.round(entry.expenses));
        const netData = incomeData.map((val, idx) => val + expenseData[idx]);
        if (this.cashFlowChart) this.cashFlowChart.destroy();
        const ctx = document.getElementById("cashFlowChart").getContext("2d");
        const datasets = this.isStackedView
          ? [
              { label: "Income", data: incomeData, backgroundColor: "#4BC0C0" },
              { label: "Expenses", data: expenseData, backgroundColor: "#FF6384" }
            ]
          : [
              {
                label: "Net Income",
                data: netData,
                backgroundColor: netData.map(value =>
                  value >= 0 ? "#4BC0C0" : "#FF6384"
                )
              }
            ];
        this.cashFlowChart = new Chart(ctx, {
          type: "bar",
          data: { labels, datasets },
          options: {
            responsive: true,
            scales: {
              x: { stacked: this.isStackedView, ticks: { autoSkip: false } },
              y: { stacked: this.isStackedView, beginAtZero: true }
            }
          }
        });
      } catch (error) {
        console.error("Error rendering cash flow chart:", error);
      }
    },
    async renderCategoryChart() {
      try {
        const response = await axios.get("/api/charts/category_breakdown");
        if (response.data.status !== "success") return;
        const data = response.data.data;
        const values = data.map(entry => Math.round(entry.amount));
        const labels = data.map(entry => entry.category);
        if (this.categoryChart) this.categoryChart.destroy();
        const ctx = document.getElementById("categoryBreakdownChart").getContext("2d");
        this.categoryChart = new Chart(ctx, {
          type: this.isCategoryPie ? "pie" : "bar",
          data: {
            labels,
            datasets: [{
              label: "Spending by Category",
              data: values,
              backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
            }]
          },
          options: {
            responsive: true,
            onClick: (event, elements) => {
              if (elements.length > 0) {
                const idx = elements[0].index;
                const category = labels[idx];
                this.filterTransactionsByCategory(category);
              }
            }
          }
        });
      } catch (error) {
        console.error("Error rendering category chart:", error);
      }
    },
    async renderNetAssetsChart() {
      try {
        const response = await axios.get("/api/charts/net_assets");
        if (response.data.status !== "success") return;
        const data = response.data.data;
        const labels = data.map(entry => entry.period);
        const assetsData = data.map(entry => Math.round(entry.assets));
        const liabilitiesData = data.map(entry => -Math.round(entry.liabilities));
        const netData = assetsData.map((val, idx) => val + liabilitiesData[idx]);
        if (this.netAssetsChart) this.netAssetsChart.destroy();
        const ctx = document.getElementById("netAssetsChart").getContext("2d");
        const datasets = this.isNetAssetsStacked
          ? [
              { label: "Assets", data: assetsData, backgroundColor: "#4BC0C0" },
              { label: "Liabilities", data: liabilitiesData, backgroundColor: "#FF6384" }
            ]
          : [
              {
                label: "Net Assets",
                data: netData,
                backgroundColor: netData.map(value =>
                  value >= 0 ? "#4BC0C0" : "#FF6384"
                )
              }
            ];
        this.netAssetsChart = new Chart(ctx, {
          type: "bar",
          data: { labels, datasets },
          options: {
            responsive: true,
            scales: {
              x: { stacked: this.isNetAssetsStacked, ticks: { autoSkip: false } },
              y: { stacked: this.isNetAssetsStacked, beginAtZero: true }
            }
          }
        });
      } catch (error) {
        console.error("Error rendering net assets chart:", error);
      }
    },
    async renderDailyCashFlowChart() {
      try {
        const response = await axios.get("/api/charts/cash_flow?granularity=daily");
        if (response.data.status !== "success") return;
        const data = response.data.data;
        const labels = data.map(entry => entry.date);
        const incomeData = data.map(entry => Math.round(entry.income));
        const expenseData = data.map(entry => -Math.round(entry.expenses));
        const netData = incomeData.map((val, idx) => val + expenseData[idx]);
        if (this.dailyCashFlowChart) this.dailyCashFlowChart.destroy();
        const ctx = document.getElementById("dailyCashFlowChart").getContext("2d");
        this.dailyCashFlowChart = new Chart(ctx, {
          data: {
            labels,
            datasets: [
              { type: "bar", label: "Income", data: incomeData, backgroundColor: "#4BC0C0" },
              { type: "bar", label: "Expenses", data: expenseData, backgroundColor: "#FF6384" },
              { type: "line", label: "Net Income", data: netData, borderColor: "#000", backgroundColor: "rgba(0,0,0,0.2)", fill: false, tension: 0.1 }
            ]
          },
          options: {
            indexAxis: "y",
            responsive: true,
            scales: {
              x: { beginAtZero: true },
              y: { ticks: { autoSkip: false } }
            },
            onClick: (event, elements) => {
              if (elements.length > 0) {
                const idx = elements[0].index;
                const selectedDate = labels[idx];
                this.filterTransactionsByDate(selectedDate);
              }
            }
          }
        });
      } catch (error) {
        console.error("Error rendering daily cash flow chart:", error);
      }
    },
    filterTransactionsByCategory(category) {
      if (category === "All") {
        this.fetchTransactions();
      } else {
        this.allTransactions = this.allTransactions.filter(tx => tx.category === category);
      }
      this.showReset = true;
    },
    filterTransactionsByDate(date) {
      this.allTransactions = this.allTransactions.filter(tx => tx.date === date);
      this.showReset = true;
      // Scroll transactions into view
      const transactionsSection = document.querySelector(".transactions");
      if (transactionsSection) {
        transactionsSection.scrollIntoView({ behavior: "smooth" });
      }
    },
    formatAmount(amount) {
      try {
        amount = parseFloat(amount);
        return amount < 0 ? `($${Math.abs(amount).toLocaleString()})` : `$${amount.toLocaleString()}`;
      } catch (e) {
        return "$0.00";
      }
    }
  },
  mounted() {
    this.fetchTransactions();
    this.renderCashFlowChart();
    this.renderCategoryChart();
    this.renderNetAssetsChart();
  }
};
</script>

<style scoped>
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f2f2f2;
}
nav.menu {
  display: flex;
  gap: 10px;
}
.visualization {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
}
.chart-cashflow,
.chart-categories,
.chart-netassets {
  flex: 1 1 300px;
  background: #fff;
  padding: 10px;
  border: 1px solid #ccc;
}
#expandedCashFlowContainer {
  position: relative;
  width: 100%;
  background: #fff;
  padding: 10px;
  border: 1px solid #ccc;
  margin-bottom: 20px;
}
#expandedCashFlowContainer button {
  position: absolute;
  top: 5px;
  right: 5px;
}
.transactions {
  margin-top: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
table th,
table td {
  padding: 8px;
  border: 1px solid #ddd;
}
footer {
  text-align: center;
  padding: 10px;
  background: #f2f2f2;
}
</style>
