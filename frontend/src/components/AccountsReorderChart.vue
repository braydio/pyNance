<template>
  <div class="accounts-reorder-chart">
    <h2>Top Accounts by Balance</h2>

    <div class="chart-summary">
      <!-- Liabilities Section -->
      <div class="group">
        <h3>Liabilities (Top 5)</h3>
        <draggable v-model="creditAccounts" :options="{ animation: 150 }" item-key="account_id">
          <template #item="{ element }">
            <div class="account-bar">
              <div class="account-info">
                <span class="account-name">{{ element.name }}</span>
                <span class="account-balance">{{ formatBalance(element.adjusted_balance) }}</span>
              </div>
              <div class="bar liabilities-bar" :style="{ width: getBarWidth(element, creditAccounts) }"></div>
            </div>
          </template>
        </draggable>
      </div>

      <!-- Assets Section -->
      <div class="group">
        <h3>Assets (Top 5)</h3>
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
      try {
        const response = await axios.get("/api/teller/transactions/get_accounts");
        if (response.data && response.data.status === "success") {
          this.accounts = response.data.data.accounts || response.data.data;
          this.filterAccounts();
        } else {
          console.error("Error fetching accounts:", response.data);
        }
      } catch (err) {
        console.error("Error fetching accounts:", err);
      }
    },
    filterAccounts() {
      if (!this.accounts.length) return;

      const credit = this.accounts
        .filter((acc) => acc.type && acc.type.toLowerCase() === "credit")
        .map((acc) => ({
          ...acc,
          adjusted_balance: -Math.abs(acc.balance),
        }))
        .sort((a, b) => Math.abs(b.adjusted_balance) - Math.abs(a.adjusted_balance));

      const depository = this.accounts
        .filter((acc) => !acc.type || acc.type.toLowerCase() !== "credit")
        .sort((a, b) => b.balance - a.balance);

      this.creditAccounts = credit.slice(0, 5);
      this.depositoryAccounts = depository.slice(0, 5);
    },
    formatBalance(balance) {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        currencySign: "accounting",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(balance);
    },
    getBarWidth(account, group) {
      const maxBalance = Math.max(...group.map(acc => Math.abs(acc.adjusted_balance || acc.balance)), 1);
      return ((Math.abs(account.adjusted_balance || account.balance) / maxBalance) * 100) + "%";
    }
  },
  computed: {
    topFiveLiabilities() {
      return this.creditAccounts.slice(0, 5);
    },
    topFiveAssets() {
      return this.depositoryAccounts.slice(0, 5);
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
  background-color: #282828;
  color: #ebdbb2;
  border-radius: 8px;
  margin: 1rem;
}
.chart-summary {
  display: flex;
  gap: 2rem;
}
.group {
  flex: 1;
}
.group h3 {
  margin-bottom: 0.5rem;
  color: #fabd2f;
  font-family: "Fira Code", monospace;
}
.account-bar {
  padding: 0.5rem;
  background-color: #3c3836;
  border-radius: 4px;
  cursor: move;
  margin-bottom: 0.5rem;
  display: flex;
  flex-direction: column;
}
.account-info {
  display: flex;
  justify-content: space-between;
  font-family: "Fira Code", monospace;
  font-size: 0.9rem;
}
.account-balance {
  font-weight: bold;
}
.bar {
  height: 10px;
  border-radius: 4px;
  background: linear-gradient(to right, #83a598, #458588);
}
.group .bar {
  background-color: #83a598;
}
.group:first-child .bar {
  background-color: #fb4934;
}
</style>
