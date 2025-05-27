<template>
  <div class="investments-page">
    <header class="text-center py-2.5">
      <nav class="flex justify-center gap-2.5 mt-2.5">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/teller-dot">Teller.IO</router-link>
        <router-link to="/accounts">Accounts</router-link>
        <router-link to="/transactions">Transactions</router-link>
        <router-link to="/settings">Settings</router-link>
      </nav>
    </header>

    <main class="max-w-[960px] mx-auto">
      <!-- Account Details Section -->
      <section id="account-details" class="bg-white p-5 mb-5 rounded shadow">
        <h2 class="mt-0">Account Details</h2>
        <button @click="refreshInvestments"
          class="bg-[#3498db] text-white border-none py-[10px] px-[20px] rounded cursor-pointer">
          Refresh Investments
        </button>
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
      <section id="visuals" class="bg-white p-5 mb-5 rounded shadow">
        <h2 class="mt-0">Investment Visuals</h2>
        <!-- Investment Performance Chart -->
        <div id="performance-chart" class="text-center mt-5">
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
import { formatAmount } from "@/utils/format";

export default {
  name: "Investments",
  setup() {
    const accounts = ref([]);
    const loadingAccounts = ref(false);
    let investmentChart = null;

    const formatCurrency = (value) => {
      return formatAmount(value);
    };

    const loadAccounts = async () => {
      loadingAccounts.value = true;
      try {
        const res = await axios.get("/api/plaid/investments");
        if (res.data.status === "success") {
          accounts.value = Object.values(res.data.investments);
        }
      } catch (error) {
        console.error("Error fetching investment accounts:", error);
      } finally {
        loadingAccounts.value = false;
      }
    };

    const refreshInvestments = async () => {
      try {
        await axios.post("/api/plaid/investments_refresh", {});
        await loadAccounts();
        renderInvestmentChart();
      } catch (error) {
        console.error("Error refreshing investments:", error);
      }
    };

    const renderInvestmentChart = async () => {
      try {
        const res = await axios.get("/api/investments/performance");
        if (res.data.status !== "success") return;

        const data = res.data.data;
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
                  callback: (value) => formatCurrency(value),
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
      formatCurrency,
    };
  },
};
</script>
