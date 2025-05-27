/ ** Marking this for deletion. Replaced by /components/UpdateTransactionsTable.vue /
<template>
  <div class="mt-5 text-gruvbox-fg">
    <h3>Transactions</h3>

    <!-- Filter Row -->
    <div class="mb-4">
      <input
        v-model="searchQuery"
        class="w-[200px] py-[0.4rem] px-[0.6rem] border border-gruvbox-border rounded bg-[#1d2021] text-gruvbox-fg focus:outline-none focus:border-gruvbox-accent"
        type="text"
        placeholder="Filter transactions..."
      />
    </div>

    <table class="border-collapse w-full">
      <thead>
        <tr>
        <th
          @click="sortTable('date')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Date
            <span v-if="sortKey === 'date'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        <th
          @click="sortTable('amount')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Amount
            <span v-if="sortKey === 'amount'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        <th
          @click="sortTable('description')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Description
            <span v-if="sortKey === 'description'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        <th
          @click="sortTable('category')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Category
            <span v-if="sortKey === 'category'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        <th
          @click="sortTable('merchant_name')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Merchant
            <span v-if="sortKey === 'merchant_name'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        <th
          @click="sortTable('account_name')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Account Name
            <span v-if="sortKey === 'account_name'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        <th
          @click="sortTable('institution_name')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Institution
            <span v-if="sortKey === 'institution_name'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        <th
          @click="sortTable('subtype')"
          class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg select-none cursor-pointer font-bold hover:bg-gruvbox-hover"
        >
            Subtype
            <span v-if="sortKey === 'subtype'">
              {{ sortOrder === 1 ? '▲' : '▼' }}
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="tx in sortedTransactions"
          :key="tx.transaction_id"
          class="even:bg-gruvbox-hover-bg"
        >
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ formatDate(tx.date) || "N/A" }}
          </td>
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ formatAmount(tx.amount) }}
          </td>
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ tx.description || "N/A" }}
          </td>
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ tx.category || "Unknown" }}
          </td>
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ tx.merchant_name || "Unknown" }}
          </td>
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ tx.account_name || "N/A" }}
          </td>
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ tx.institution_name || "N/A" }}
          </td>
          <td class="p-2 border border-gruvbox-border text-left bg-gruvbox-bg">
            {{ tx.subtype || "N/A" }}
          </td>
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
