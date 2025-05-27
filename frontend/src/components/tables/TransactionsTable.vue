/ ** Marking this for deletion. Replaced by /components/UpdateTransactionsTable.vue /
<template>
  <div class="transactions">
    <h3>Transactions</h3>

    <!-- Filter Row -->
    <div class="filter-row">
      <input v-model="searchQuery" class="filter-input" type="text" placeholder="Filter transactions..." />
    </div>

    <table>
      <thead>
        <tr>
          <th @click="sortTable('date')">
            Date
            <span v-if="sortKey === 'date'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
          <th @click="sortTable('amount')">
            Amount
            <span v-if="sortKey === 'amount'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
          <th @click="sortTable('description')">
            Description
            <span v-if="sortKey === 'description'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
          <th @click="sortTable('category')">
            Category
            <span v-if="sortKey === 'category'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
          <th @click="sortTable('merchant_name')">
            Merchant
            <span v-if="sortKey === 'merchant_name'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
          <th @click="sortTable('account_name')">
            Account Name
            <span v-if="sortKey === 'account_name'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
          <th @click="sortTable('institution_name')">
            Institution
            <span v-if="sortKey === 'institution_name'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
          <th @click="sortTable('subtype')">
            Subtype
            <span v-if="sortKey === 'subtype'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="tx in sortedTransactions" :key="tx.transaction_id">
          <td>{{ formatDate(tx.date) || "N/A" }}</td>
          <td>{{ formatAmount(tx.amount) }}</td>
          <td>{{ tx.description || "N/A" }}</td>
          <td>{{ tx.category || "Unknown" }}</td>
          <td>{{ tx.merchant_name || "Unknown" }}</td>
          <td>{{ tx.account_name || "N/A" }}</td>
          <td>{{ tx.institution_name || "N/A" }}</td>
          <td>{{ tx.subtype || "N/A" }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="sortedTransactions.length === 0">
      No transactions found.
    </div>
  </div>
</template>

<script>
export default {
  name: "TransactionsTable",
  props: {
    transactions: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      // Sorting & filtering
      searchQuery: "",
      sortKey: "",
      sortOrder: 1, // 1 = asc, -1 = desc
    };
  },
  computed: {
    filteredTransactions() {
      if (!this.searchQuery.trim()) {
        return this.transactions;
      }
      const query = this.searchQuery.toLowerCase();
      return this.transactions.filter((tx) => {
        const fields = [
          tx.date,
          tx.description,
          tx.category,
          tx.merchant_name,
          tx.account_name,
          tx.institution_name,
          tx.subtype,
        ].map((val) => (val || "").toString().toLowerCase());
        return fields.some((field) => field.includes(query));
      });
    },
    sortedTransactions() {
      const sorted = [...this.filteredTransactions];
      if (!this.sortKey) {
        return sorted;
      }
      sorted.sort((a, b) => {
        let valA = a[this.sortKey];
        let valB = b[this.sortKey];

        // Convert to lower case if string
        if (typeof valA === "string") valA = valA.toLowerCase();
        if (typeof valB === "string") valB = valB.toLowerCase();

        if (valA < valB) return -1 * this.sortOrder;
        if (valA > valB) return 1 * this.sortOrder;
        return 0;
      });
      return sorted;
    },
  },
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return "N/A";
      const date = new Date(dateStr);
      return date.toLocaleDateString("en-US", {
        year: "2-digit",
        month: "short",
        day: "numeric"
      });
    },
    formatAmount(amount) {
      const number = parseFloat(amount);
      const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        currencySign: "accounting",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return formatter.format(number);
    },
    sortTable(key) {
      if (this.sortKey === key) {
        this.sortOrder = -this.sortOrder; // flip asc/desc
      } else {
        this.sortKey = key;
        this.sortOrder = 1; // reset to ascending
      }
    },
  },
};
</script>

<style scoped>
@import '@/styles/global-colors.css';

.transactions {
  margin-top: 20px;
  color: var(--gruvbox-fg);
}

/* Filter input styling */
.filter-row {
  margin-bottom: 1rem;
}

.filter-input {
  width: 200px;
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--gruvbox-border);
  border-radius: 4px;
  background-color: #1d2021;
  color: var(--gruvbox-fg);
  outline: none;
}

.filter-input:focus {
  border-color: var(--gruvbox-accent);
}

/* Table styling */
table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 1px solid var(--gruvbox-border);
  padding: 8px;
  text-align: left;
  background-color: var(--gruvbox-bg);
  user-select: none;
}

th {
  cursor: pointer;
  font-weight: bold;
}

th:hover {
  background-color: var(--gruvbox-hover);
}

/* Zebra striping on even rows */
tbody tr:nth-child(even) {
  background-color: var(--gruvbox-hover-bg);
}
</style>
