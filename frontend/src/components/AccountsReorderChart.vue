<template>
  <div class="accounts-reorder-chart">
    <h2>Top Accounts by Balance</h2>
    <div class="chart-summary">
      <!-- Liabilities Section -->
      <div class="group">
        <h3>Liabilities (Credit Accounts)</h3>
        <draggable v-model="creditAccounts" :options="{ animation: 150 }" item-key="account_id">
          <template #item="{ element }">
            <div class="account-bar">
              <div class="account-info">
                <span class="account-name">{{ element.name }}</span>
                <span class="account-balance">
                  {{ formatBalance(element.adjusted_balance) }} <!-- Now always correct -->
                </span>
              </div>
              <div class="bar" :style="{ width: getBarWidth(element, creditAccounts) }"></div>
            </div>
          </template>
        </draggable>
      </div>

      <!-- Assets Section -->
      <div class="group">
        <h3>Assets (Depository Accounts)</h3>
        <draggable v-model="depositoryAccounts" :options="{ animation: 150 }" item-key="account_id">
          <template #item="{ element }">
            <div class="account-bar">
              <div class="account-info">
                <span class="account-name">{{ element.name }}</span>
                <span class="account-balance">
                  {{ formatBalance(element.balance) }}
                </span>
              </div>
              <div class="bar" :style="{ width: getBarWidth(element, depositoryAccounts) }"></div>
            </div>
          </template>
        </draggable>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import draggable from "vuedraggable";

export default {
  name: "AccountsReorderChart",
  components: { draggable },
  data() {
    return {
      accounts: [],
      creditAccounts: [],
      depositoryAccounts: [],
    };
  },
  methods: {
    async fetchAccounts() {
      console.log("Fetching accounts...");
      try {
        const response = await axios.get("/api/teller/transactions/get_accounts");
        console.log("Response from /api/teller/get_accounts:", response.data);
        if (response.data && response.data.status === "success") {
          this.accounts = response.data.data.accounts || response.data.data;
          console.log("Accounts fetched:", this.accounts.length);
          this.filterAccounts();
        } else {
          console.error("Error fetching accounts:", response.data);
        }
      } catch (err) {
        console.error("Error fetching accounts:", err);
      }
    },
    filterAccounts() {
      if (!this.accounts.length) {
        console.warn("No accounts to filter.");
        return;
      }

      // Classify accounts into liabilities (credit) and assets (depository)
      const credit = this.accounts
        .filter((acc) => acc.type && acc.type.toLowerCase() === "credit")
        .map((acc) => ({
          ...acc,
          adjusted_balance: acc.balance > 0 ? acc.balance : -Math.abs(acc.balance), // ✅ Always negative unless credit
        }));

      const depository = this.accounts.filter(
        (acc) => !acc.type || acc.type.toLowerCase() !== "credit"
      );

      // Sort liabilities by absolute balance
      credit.sort((a, b) => Math.abs(b.adjusted_balance) - Math.abs(a.adjusted_balance));
      depository.sort((a, b) => b.balance - a.balance);

      // Limit to top 10 items per group
      this.creditAccounts = credit.slice(0, 10);
      this.depositoryAccounts = depository.slice(0, 10);

      console.log("Liabilities (Adjusted):", this.creditAccounts);
      console.log("Assets:", this.depositoryAccounts);
    },
    formatBalance(balance) {
      const number = parseFloat(balance);
      const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        currencySign: "accounting", // Uses parentheses for negatives
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return formatter.format(number);
    },
    getBarWidth(account, group) {
      // Calculate width relative to the maximum absolute balance in the group
      const maxBalance = Math.max(...group.map(acc => Math.abs(acc.adjusted_balance || acc.balance)), 1);
      const widthPercent = (Math.abs(account.adjusted_balance || account.balance) / maxBalance) * 100;
      return widthPercent + "%";
    }
  },
  mounted() {
    this.fetchAccounts();
  }
};
</script>



<style scoped>
.accounts-reorder-chart {
  padding: 1rem;
  background-color: #282828; /* Gruvbox dark background */
  color: #ebdbb2; /* Gruvbox light text */
  border-radius: 8px;
  margin: 1rem;
}
.chart-summary {
  display: flex;
  gap: 1rem;
}
.group {
  flex: 1;
}
.group h3 {
  margin-bottom: 0.5rem;
  color: #fabd2f; /* Accent yellow */
  font-family: "Fira Code", monospace;
}
.account-bar {
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background-color: #3c3836;
  border-radius: 4px;
  cursor: move;
  display: flex;
  flex-direction: column;
}
.account-info {
  display: flex;
  justify-content: space-between;
  font-family: "Fira Code", monospace;
  font-size: 0.9rem;
  margin-bottom: 0.3rem;
}
.account-balance {
  font-weight: bold;
}
.bar {
  height: 10px;
  border-radius: 4px;
}
</style>
