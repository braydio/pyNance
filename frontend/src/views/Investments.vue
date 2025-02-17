<template>
    <div class="investments-page">
      <header>
        <div>
          <h1>Accounts</h1>
          <h3>dot Brayden.com</h3>
        </div>
        <nav class="menu">
          <router-link to="/">Dashboard</router-link>
          <router-link to="/accounts">Accounts</router-link>
          <router-link to="/transactions">Transactions</router-link>
          <router-link to="/settings">Settings</router-link>
        </nav>
      </header>
  
      <main>
        <!-- Account Details Section -->
        <section id="account-details">
          <h2>Account Details</h2>
          <button @click="refreshInvestments">Refresh Investments</button>
          <!-- Here we render the list of investment accounts -->
          <div id="accounts-list">
            <div v-if="loadingAccounts">Loading accounts…</div>
            <div v-else-if="accounts.length === 0">
              No investment accounts found.
            </div>
            <ul v-else>
              <li v-for="account in accounts" :key="account.id">
                <strong>{{ account.name }}</strong> – {{ account.balance | currency }}
              </li>
            </ul>
          </div>
        </section>
  
        <!-- Visual Selections Section -->
        <section id="visuals">
          <h2>Investment Visuals</h2>
          <!-- Investment Performance Chart -->
          <div id="performance-chart">
            <canvas id="investmentChart" width="800" height="400"></canvas>
          </div>
          <!-- You can add more visual components here (e.g. pie charts, etc.) -->
        </section>
      </main>
    </div>
  </template>
  
  <script>
  import { ref, onMounted } from "vue";
  import Chart from "chart.js/auto";
  import axios from "axios";
  
  // Optionally, you can import a currency filter from your utilities
  import { formatAmount } from "../utils/format";
  
  export default {
    name: "Investments",
    setup() {
      // State for investment accounts
      const accounts = ref([]);
      const loadingAccounts = ref(false);
  
      // Reference for Chart.js instance
      let investmentChart = null;
  
      // Method to load investment accounts from the backend
      const loadAccounts = async () => {
        loadingAccounts.value = true;
        try {
          // Replace the URL with your actual endpoint for investments
          const res = await axios.get("/api/plaid/investments");
          if (res.data.status === "success") {
            // Assume res.data.investments is an array of account objects
            accounts.value = Object.values(res.data.investments);
          }
        } catch (error) {
          console.error("Error fetching investment accounts:", error);
        } finally {
          loadingAccounts.value = false;
        }
      };
  
      // Method to refresh investment data (could call an API endpoint)
      const refreshInvestments = async () => {
        try {
          // Call your refresh API for investments if available
          await axios.post("/api/plaid/investments_refresh", {
            // Pass required parameters such as item_id if needed
          });
          // Reload accounts after refresh
          await loadAccounts();
          // Optionally, re-render charts here.
          renderInvestmentChart();
        } catch (error) {
          console.error("Error refreshing investments:", error);
        }
      };
  
      // Method to render the investment performance chart using Chart.js
      const renderInvestmentChart = async () => {
        try {
          // Fetch performance data from your backend API
          const res = await axios.get("/api/investments/performance");
          if (res.data.status !== "success") return;
          const data = res.data.data; // Assume an array with { date, performance } entries
  
          const labels = data.map((entry) => entry.date);
          const performanceData = data.map((entry) => entry.performance);
  
          if (investmentChart) {
            investmentChart.destroy();
          }
          const ctx = document.getElementById("investmentChart").getContext("2d");
          investmentChart = new Chart(ctx, {
            type: "line",
            data: {
              labels,
              datasets: [
                {
                  label: "Investment Performance",
                  data: performanceData,
                  borderColor: "#3498db",
                  backgroundColor: "rgba(52, 152, 219, 0.2)",
                  fill: true,
                  tension: 0.1,
                },
              ],
            },
            options: {
              responsive: true,
              scales: {
                x: { display: true },
                y: {
                  display: true,
                  ticks: {
                    callback: (value) => formatAmount(value),
                  },
                },
              },
            },
          });
        } catch (error) {
          console.error("Error rendering investment chart:", error);
        }
      };
  
      onMounted(async () => {
        await loadAccounts();
        renderInvestmentChart();
      });
  
      return {
        accounts,
        loadingAccounts,
        refreshInvestments,
      };
    },
    filters: {
      currency(value) {
        return formatAmount(value);
      },
    },
  };
  </script>
  
  <style scoped>
  body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background: #f4f4f4;
  }
  header,
  main {
    max-width: 960px;
    margin: auto;
  }
  header {
    text-align: center;
    padding: 10px 0;
  }
  nav.menu {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 10px;
  }
  section {
    background: #fff;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  h2 {
    margin-top: 0;
  }
  button {
    background: #3498db;
    color: #fff;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
  }
  #performance-chart {
    text-align: center;
    margin-top: 20px;
  }
  </style>
  