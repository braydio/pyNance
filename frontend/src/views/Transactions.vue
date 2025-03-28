<template>
  <div class="transactions-page">
    <header>
      <div>
        <h1>Transactions</h1>
        <h3>View and manage your transactions</h3>
        <div>        
        <RecurringTransactionSection provider="plaid" />

      </div>
      </div>
    </header>
    <main>
      <div class="controls">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search transactions..."
          class="search-input"
        />
      </div>
      <TransactionsTable
        :transactions="filteredTransactions"
        :sort-key="sortKey"
        :sort-order="sortOrder"
        @sort="setSort"
      />
      <div id="pagination-controls">
        <button @click="changePage(-1)" :disabled="currentPage === 1">Previous</button>
        <span>Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="changePage(1)" :disabled="currentPage >= totalPages">Next</button>
      </div>
    </main>
  </div>
</template>

<script>
import { useTransactions } from "@/composables/useTransactions.js";
import TransactionsTable from "../components/UpdateTransactionsTable.vue";

export default {
  name: "Transactions",
  components: { TransactionsTable },
  setup() {
    const {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
    } = useTransactions(15);

    return {
      searchQuery,
      currentPage,
      totalPages,
      filteredTransactions,
      changePage,
      sortKey,
      sortOrder,
      setSort,
    };
  },
};
</script>

<style scoped>
@import '@/styles/global-colors.css';

.transactions-page {
  padding: 20px;
}
.controls {
  margin-bottom: 10px;
}
.search-input {
  padding: 8px;
  width: 100%;
  max-width: 300px;
}
#pagination-controls {
  margin-top: 10px;
  text-align: center;
}
button {
  padding: 8px 12px;
  background-color: #007bff;
  color: white;
  border: none;
  cursor: pointer;
}
button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
button:hover:not(:disabled) {
  background-color: #0056b3;
}

</style>
