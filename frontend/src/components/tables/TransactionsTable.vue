<template>
  <div class="mt-6 text-primary font-mono">
    <h3 class="text-xl font-bold mb-4 text-accent-yellow">Transactions</h3>

    <!-- Search -->
    <div class="mb-4">
      <input v-model="searchQuery"
        class="w-[250px] py-2 px-3 border border-secondary rounded bg-dark text-primary focus:outline-none focus:border-accent-yellow transition"
        type="text" placeholder="Search transactions, account, institution..." />
    </div>

    <div class="overflow-auto rounded-xl border border-secondary bg-dark shadow-none">
      <table class="min-w-full table-auto border-collapse">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key" @click="sortTable(col.key)"
              class="px-4 py-3 text-left select-none cursor-pointer font-bold uppercase text-xs tracking-wide border-b border-secondary bg-secondary transition"
              :class="[
                col.key === 'amount' ? 'text-accent-green' :
                  col.key === 'date' ? 'text-accent-cyan' :
                    col.key === 'account' ? 'text-accent-yellow' :
                      col.key === 'descriptionMerchant' ? 'text-accent-orange' :
                        'text-primary'
              ]" :style="{ minWidth: col.key === 'descriptionMerchant' ? '220px' : '120px' }">
              {{ col.label }}
              <span v-if="sortKey === col.key" class="ml-1 font-black text-accent-yellow">
                {{ sortOrder === 1 ? '▲' : '▼' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(tx, idx) in sortedTransactions" :key="tx.transaction_id" :class="[
            idx % 2 === 0 ? 'bg-dark' : 'bg-secondary',
            'hover:bg-frosted-bg transition'
          ]">
            <td class="px-4 py-2 text-xs text-accent-cyan font-mono">
              {{ formatDate(tx.date) || "N/A" }}
            </td>
            <td class="px-4 py-2 font-semibold whitespace-nowrap font-mono"
              :class="tx.amount < 0 ? 'text-error' : 'text-accent-green'">
              {{ formatAmount(tx.amount) }}
            </td>
            <td class="px-4 py-2 text-xs text-accent-yellow font-bold">
              {{ [tx.institution_name, tx.account_name].filter(Boolean).join(' • ') || "N/A" }}
            </td>
            <td class="px-4 py-2 text-xs text-primary">
              {{ tx.category || "Unknown" }}
            </td>
            <td class="px-4 py-2 max-w-xs text-sm text-primary truncate"
              :title="(tx.merchant_name ? tx.merchant_name + ': ' : '') + (tx.description || 'N/A')">
              <span v-if="tx.merchant_name"><b>{{ tx.merchant_name }}:</b> </span>{{ tx.description || "N/A" }}
            </td>
          </tr>
          <tr v-if="sortedTransactions.length === 0">
            <td :colspan="columns.length" class="px-4 py-10 text-center text-muted bg-dark">
              No transactions found.
            </td>
          </tr>
        </tbody>
      </table>
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
      columns: [
        { key: 'date', label: 'Date' },
        { key: 'amount', label: 'Amount' },
        { key: 'description', label: 'Description' },
        { key: 'category', label: 'Category' },
        { key: 'institutionAccount', label: 'Account' }, // Concatenated column
        { key: 'merchant_name', label: 'Merchant' },
        { key: 'subtype', label: 'Subtype' }
      ]
    };
  },
  computed: {
    filteredTransactions() {
      if (!this.searchQuery.trim()) {
        return this.transactions;
      }
      const query = this.searchQuery.toLowerCase();
      return this.transactions.filter((tx) => {
        // Concatenate institution + account for searching
        const institutionAccount = [tx.institution_name, tx.account_name].filter(Boolean).join(" ");
        const fields = [
          tx.date,
          tx.description,
          tx.category,
          tx.merchant_name,
          tx.subtype,
          institutionAccount
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
        let valA, valB;
        if (this.sortKey === "institutionAccount") {
          valA = [a.institution_name, a.account_name].filter(Boolean).join(" ");
          valB = [b.institution_name, b.account_name].filter(Boolean).join(" ");
        } else {
          valA = a[this.sortKey];
          valB = b[this.sortKey];
        }
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
